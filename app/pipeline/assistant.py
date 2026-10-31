"""The question-to-response pipeline. The code decides every step; the model only phrases.

Stages, always in this order:
 1. language        2. intent              3. out-of-scope routing
 4. clarification   5. retrieval           6. evidence validation
 7. rules           8. fixed rule sentences + model draft
 9. verification (cannot be bypassed; failed text is replaced by quoted evidence)
10. escalation for decisions, exceptions and personal records
"""
import logging

from app.evidence.validator import validate_evidence
from app.generation.answer_generator import base_response, non_answer
from app.generation.extractive import evidence_fits, overlap_scorer, relevance_filter, select_sentences
from app.generation.rule_sentences import event_sentence, rule_sentence, statement_sentences
from app.generation.templates import QUOTE_INTRO
from app.intent.ambiguity import SCOPE_TO_INTENT, apply_clarification, clarified_query, detect_missing
from app.intent.context_extractor import extract_context
from app.intent.language import answer_language, detect_language
from app.rules.event_lookup import calendar_event_result
from app.rules.selection import extract_inputs, run_rules
from app.safety.escalation import NEXT_STEP, escalation_block, escalation_reason, record_escalation
from app.documents.injection import injection_signals
from app.safety.sentence_filter import filter_items, filter_sentences
from app.safety.verifier import contradicts_rules

log = logging.getLogger(__name__)


def _source_refs(chunks):
    return [{"source_id": c["source_id"], "chunk_id": c["chunk_id"], "page": c.get("page"),
             "section": c.get("section")} for c in chunks]


class Assistant:
    """Answer one question about one date, safely."""

    def __init__(self, classifier, retriever, engine, generator, sources_by_id, top_k=5,
                 scorer=overlap_scorer, escalation_log=None, glossary=()):
        self.classifier, self.retriever, self.engine = classifier, retriever, engine
        self.generator, self.sources_by_id, self.top_k = generator, sources_by_id, top_k
        self.scorer, self.escalation_log, self.glossary = scorer, escalation_log, list(glossary)

    def answer(self, question, as_of, clarification=None):
        """Return a verified schema response.

        Args:
            question: the student question.
            as_of: the date the question is about (an input, never the clock).
            clarification: values from a clarification reply, for example
                {"withdrawal_scope": "semester"} or {"degree_level": "master"}.
        """
        supplied = dict(clarification or {})
        trace = {"language_detected": detect_language(question), "clarification": supplied}
        language = answer_language(question)

        intent = self.classifier.classify(question)
        trace["intent_classified"] = intent
        if escalation_reason(question) == "third_party":
            return self._escalate("third_party", intent, language, as_of, [], [], trace)
        if intent == "OUT_OF_SCOPE" and detect_missing(question, "WITHDRAWAL_UNSPECIFIED", supplied):
            intent = "WITHDRAWAL_UNSPECIFIED"  # a generic withdrawal question is never out of scope (v1: E071, E072)
            trace["intent_rerouted"] = intent
        if intent == "OUT_OF_SCOPE":
            return self._finish(non_answer("OUT_OF_SCOPE", intent, language, as_of), trace, "templated")

        values = dict(extract_context(question, intent)["values"])
        if values.get("degree_level"):
            values["degree"] = values["degree_level"]  # rules read "degree" (v1: E061 rule returned unknown)
        if supplied.get("degree_level"):
            values["degree"] = supplied["degree_level"]
        if supplied.get("withdrawal_scope"):
            values["withdrawal_scope"] = supplied["withdrawal_scope"]
        if intent == "WITHDRAWAL_UNSPECIFIED" and values.get("withdrawal_scope"):
            intent = SCOPE_TO_INTENT[values["withdrawal_scope"]]
        missing = detect_missing(question, intent, supplied)
        if missing:
            return self._finish(non_answer("CLARIFICATION_REQUIRED", intent, language, as_of, missing=[missing]),
                                trace, "templated")
        intent = apply_clarification(intent, supplied)
        trace["intent"] = intent

        query = clarified_query(question, supplied)
        chunks = self.retriever.search(query, as_of, "hybrid", self.top_k)
        trace["retrieved"] = [c["chunk_id"] for c in chunks]
        # Second line of defence after the ingest scanner: text addressed to the model never becomes evidence.
        trace["quarantined"] = [c["chunk_id"] for c in chunks if injection_signals(c["text"])]
        chunks = [c for c in chunks if c["chunk_id"] not in trace["quarantined"]]
        report = validate_evidence(intent, query, chunks, self.sources_by_id, as_of)
        trace.update(evidence_status=report["status"], off_topic=[o["chunk_id"] for o in report["off_topic"]],
                     overridden=report["overridden_chunks"])

        context = {"values": values}
        rules = run_rules(self.engine, intent, question, context, as_of)
        if intent == "ACADEMIC_CALENDAR":
            event = calendar_event_result(getattr(self.engine, "calendar", None), question, as_of, values.get("term"))
            if event:
                rules.append(event)
        inputs = extract_inputs(question, context)
        stated_values = {k for k, v in inputs.items() if v is not None}
        for rule_id, sentence in statement_sentences(question, language, values.get("degree"), stated_values):
            rules.append({"rule_id": rule_id, "output": "stated", "details": {"statement": sentence},
                          "sources": self.engine.rules[rule_id]["sources"], "as_of": str(as_of)})
        rule_texts = [t for t in (self._rule_text(r, language, inputs) for r in rules) if t]
        trace["rules"] = [(r["rule_id"], r["output"]) for r in rules]

        # A rule computed from the calendar or stated from the rule library does not depend on
        # search: missing search results must not block it (v1: E012, E013, A04).
        backed = [r for r in rules if r["output"] not in ("unknown", "not_applicable")]
        unresolved_conflict = any(c["winner"] is None for c in report["conflicts"])
        if report["status"] == "INSUFFICIENT_EVIDENCE" and backed and not unresolved_conflict:
            report = {**report, "status": "OK", "evidence": report["evidence"] + self._calendar_chunks(backed, report["evidence"])}
            trace["evidence_status"] = "OK (rule-backed)"
        # A deadline asked about with no calendar in force for that date cannot be answered from
        # the regulation alone; the model must never fill the gap (held-out: H040 said "you can still withdraw").
        no_calendar = [r for r in rules if r["rule_id"].startswith("RULE-CAL") and r["output"] == "unknown"
                       and "calendar" in str(r["details"].get("reason", ""))]
        if no_calendar and not any(r["output"] in ("open", "closed", "refund_eligible", "refund_not_eligible")
                                   for r in rules):
            trace["no_calendar"] = [r["rule_id"] for r in no_calendar]
            report = {**report, "status": "INSUFFICIENT_EVIDENCE"}
            trace["evidence_status"] = "INSUFFICIENT_EVIDENCE (no calendar in force)"
        early_reason = escalation_reason(question, rules)
        if report["status"] != "OK":
            if early_reason:
                return self._escalate(early_reason, intent, language, as_of, [], [], trace)
            unresolved = [c for c in report["conflicts"] if c["winner"] is None]
            return self._finish(non_answer(report["status"], intent, language, as_of, conflicts=unresolved),
                                trace, "templated")

        if not rule_texts and not evidence_fits(question, [c["text"] for c in report["evidence"]], self.glossary):
            trace["gate"] = "no evidence passage shares the question's key terms"
            if early_reason:
                return self._escalate(early_reason, intent, language, as_of, [], [], trace)
            return self._finish(non_answer("INSUFFICIENT_EVIDENCE", intent, language, as_of), trace, "templated")

        response = self._compose(question, intent, language, as_of, report["evidence"], rules, rule_texts, trace)
        if response["status"] != "ANSWERABLE":
            # A request for a decision is escalated even when nothing could be confirmed (held-out: H034).
            if early_reason:
                return self._escalate(early_reason, intent, language, as_of, [], [], trace)
            return self._finish(response, trace, "templated")
        reason = escalation_reason(question, rules)
        if reason:
            confirmed = [response["answer"]]
            return self._escalate(reason, intent, language, as_of, confirmed, response["sources"], trace,
                                  rule_outputs=response["rule_outputs"])
        return self._finish(response, trace, trace["mode"])

    @staticmethod
    def _rule_text(result, language, inputs):
        if result["rule_id"] == "CAL-EVENT":
            return event_sentence(result["details"], language)
        if result["output"] == "stated":
            return result["details"]["statement"]
        return rule_sentence(result, language, inputs)

    def _all_chunks(self):
        r = self.retriever
        while not hasattr(r, "chunks") and hasattr(r, "inner"):
            r = r.inner
        return getattr(r, "chunks", [])

    def _calendar_chunks(self, results, have):
        """Return the calendar rows behind calendar rule results, so the answer cites them."""
        wanted = {(r["details"].get("calendar"), f"row {r['details'].get('calendar_row')}") for r in results
                  if r["details"].get("calendar")}
        held = {c["chunk_id"] for c in have}
        return [c for c in self._all_chunks() if (c["source_id"], c.get("section")) in wanted and c["chunk_id"] not in held]

    def _compose(self, question, intent, language, as_of, evidence, rules, rule_texts, trace):
        """Fixed rule sentences, then model sentences that pass every check, else quoted evidence."""
        r = base_response("ANSWERABLE", intent, language, as_of)
        r["rule_outputs"] = [{k: x[k] for k in ("rule_id", "output", "details")} for x in rules]
        rule_sources = [dict(s) for x in rules for s in x["sources"]]
        try:
            draft = self.generator.draft(question, language, as_of, evidence, rules, rule_texts)
        except ValueError as e:
            draft = None
            trace["verification_issues"] = [f"model output unusable: {e}"]
        except Exception as e:  # timeout or model down: answer from rule sentences and quotes only, never crash
            log.warning("model unavailable while drafting (%s); using rule sentences and quoted evidence", type(e).__name__)
            draft = None
            trace["verification_issues"] = [f"model unavailable: {type(e).__name__}"]
        kept = []
        if draft is not None:
            context = dict(language=language, evidence_texts=[c["text"] for c in draft["given"]],
                           rule_outputs=rules, rule_texts=rule_texts, intent=intent,
                           glossary=self.glossary, question=question)
            kept, dropped = filter_sentences(draft["explanation"], **context)
            action, _ = filter_sentences(draft["required_action"], **context)
            r["conditions"] = filter_items(draft["conditions"], **context)
            r["required_action"] = " ".join(action)
            trace["verification_issues"] = [f"{s[:60]}... -> {', '.join(i)}" for s, i in dropped]
            trace["sentences_kept"] = len(kept)
        trace["rule_texts"] = list(rule_texts)
        if kept:
            trace["mode"] = "generated"
            r["answer"] = " ".join(rule_texts + kept)
            r["sources"] = _source_refs(draft["used"])
            trace["claims_generated"] = list(kept)
        else:
            relevant = relevance_filter(question, self.glossary)
            quotes = select_sentences(question, evidence, self.scorer, k=2,
                                      qualifies=lambda s: relevant(s) and not contradicts_rules(s, rules))
            if not quotes and not rule_texts:
                return non_answer("INSUFFICIENT_EVIDENCE", intent, language, as_of)
            trace["mode"] = "extractive"
            quoted = " ".join(f"«{s}»" for s, _ in quotes)
            r["answer"] = " ".join(rule_texts + ([f"{QUOTE_INTRO[language]} {quoted}"] if quotes else []))
            r["sources"] = _source_refs([c for _, c in quotes])
            r["conditions"], r["required_action"] = [], ""
            trace["quotes"] = [{"text": q, "chunk_id": c["chunk_id"]} for q, c in quotes]
        for s in rule_sources:
            if s not in r["sources"]:
                r["sources"].append(s)
        return r

    def _escalate(self, reason, intent, language, as_of, confirmed, sources, trace, rule_outputs=()):
        """Return STAFF_REVIEW_REQUIRED with what can be confirmed and where to go."""
        r = base_response("STAFF_REVIEW_REQUIRED", intent, language, as_of)
        block = escalation_block(reason, language, confirmed, sources)
        r.update(answer=block["reason"], required_action=NEXT_STEP[language], sources=list(sources),
                 escalation=block, rule_outputs=list(rule_outputs))
        if self.escalation_log:
            record_escalation(self.escalation_log, reason, intent, sources, as_of)
        return self._finish(r, trace, "escalated")

    @staticmethod
    def _finish(response, trace, mode):
        """Mark the response as having passed the verification stage and attach the trace."""
        trace["mode"] = mode
        return {**response, "verified": True, "_trace": trace}
