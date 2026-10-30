"""Build responses: fixed templates for non-answers, the local model for answers."""
import json
import logging

from app.generation.templates import CLARIFY, CONTACT, DATE_BASIS, TEXTS
from app.models.prompts import fill, load_prompt

log = logging.getLogger(__name__)
LANGUAGE_NAMES = {"ar": "Arabic (العربية)", "en": "English"}


def base_response(status, intent, language, as_of):
    """Return a response with every schema field set to its empty value."""
    return {"status": status, "intent": intent, "language": language, "as_of": str(as_of),
            "answer": "", "conditions": [], "required_action": "", "rule_outputs": [],
            "sources": [], "date_basis": DATE_BASIS[language].format(as_of=as_of),
            "clarification": None, "escalation": None, "verified": False}


def non_answer(status, intent, language, as_of, conflicts=None, missing=None):
    """Return a fixed-text response for a status other than ANSWERABLE.

    Args:
        status: CLARIFICATION_REQUIRED, INSUFFICIENT_EVIDENCE, CONFLICTING_EVIDENCE or OUT_OF_SCOPE.
        intent: the classified intent.
        language: "ar" or "en".
        as_of: the date the question is about.
        conflicts: unresolved conflicts, listed as sources when the status is CONFLICTING_EVIDENCE.
        missing: missing context fields, used to choose the clarification question.
    """
    r = base_response(status, intent, language, as_of)
    if status == "CLARIFICATION_REQUIRED":
        field = (missing or ["withdrawal_scope"])[0]
        r["answer"] = CLARIFY[field][language]
        r["clarification"] = {"missing": field, "question": CLARIFY[field][language]}
        return r
    r["answer"] = TEXTS[status][language]
    r["required_action"] = CONTACT[language]
    for c in conflicts or []:
        for source_id, chunk_id in c["chunks"].items():
            r["sources"].append({"source_id": source_id, "chunk_id": chunk_id, "value": c["values"][source_id]})
    return r


def _rules_text(rule_outputs):
    """Describe rule results as plain lines the model must restate."""
    if not rule_outputs:
        return "(none)"
    lines = []
    for r in rule_outputs:
        d = r["details"]
        extra = f", date {d['date']} ({d['hijri']} AH), term {d['term_id']}" if "date" in d else ""
        lines.append(f"- {r['rule_id']}: result = {r['output']}{extra}; details = {json.dumps(d, ensure_ascii=False)}")
    return "\n".join(lines)


class AnswerGenerator:
    """Ask the local model to phrase an answer from evidence and rule outputs."""

    def __init__(self, client, prompts_dir="prompts", evidence_limit=3, evidence_chars=700):
        self.client = client
        self.header, self.template = load_prompt("answer_v1", prompts_dir)
        _, self.glossary = load_prompt("glossary_v1", prompts_dir)
        self.evidence_limit, self.evidence_chars = evidence_limit, evidence_chars

    def answer(self, question, intent, language, as_of, evidence, rule_outputs, conditions):
        """Return an ANSWERABLE response whose content comes from the given evidence.

        Sources are attached by code from the evidence the model says it used;
        if it names none, every passage it was given is cited.
        """
        used = evidence[: self.evidence_limit]
        labelled = {f"E{i}": c for i, c in enumerate(used, 1)}
        evidence_text = "\n\n".join(
            f"[{label}] {c['source_id']} (page {c.get('page')}, {c.get('section') or ''}):\n"
            f"{' '.join(c['text'].split())[: self.evidence_chars]}"
            for label, c in labelled.items())
        prompt = fill(self.template, language_name=LANGUAGE_NAMES[language], glossary=self.glossary,
                      as_of=as_of, question=question, rules=_rules_text(rule_outputs), evidence=evidence_text)
        r = base_response("ANSWERABLE", intent, language, as_of)
        r["rule_outputs"] = [{k: x[k] for k in ("rule_id", "output", "details")} for x in rule_outputs]
        try:
            output = self.client.generate_json(prompt)
        except ValueError as e:
            log.warning("model output unusable, answering INSUFFICIENT_EVIDENCE: %s", e)
            return non_answer("INSUFFICIENT_EVIDENCE", intent, language, as_of)
        r["answer"] = str(output.get("answer", "")).strip()
        r["conditions"] = [str(c) for c in output.get("conditions", []) if str(c).strip()]
        r["required_action"] = str(output.get("required_action", "")).strip()
        cited = [labelled[e] for e in output.get("used_evidence", []) if e in labelled] or used
        r["sources"] = [{"source_id": c["source_id"], "chunk_id": c["chunk_id"],
                         "page": c.get("page"), "section": c.get("section")} for c in cited]
        for x in rule_outputs:
            for s in x["sources"]:
                if s not in r["sources"]:
                    r["sources"].append(dict(s))
        r["_evidence_given"] = [c["chunk_id"] for c in used]
        r["_condition_candidates"] = [c["text"] for c in conditions]
        if not r["answer"]:
            return non_answer("INSUFFICIENT_EVIDENCE", intent, language, as_of)
        return r
