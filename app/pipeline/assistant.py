"""The question-to-response pipeline; the code, not the model, decides each step."""
import logging

from app.evidence.validator import validate_evidence
from app.generation.answer_generator import non_answer
from app.intent.context_extractor import extract_context
from app.intent.language import answer_language, detect_language
from app.rules.selection import run_rules

log = logging.getLogger(__name__)


class Assistant:
    """Run the fixed sequence of stages for one question on one date."""

    def __init__(self, classifier, retriever, engine, generator, sources_by_id, top_k=5):
        self.classifier, self.retriever = classifier, retriever
        self.engine, self.generator = engine, generator
        self.sources_by_id, self.top_k = sources_by_id, top_k

    def answer(self, question, as_of):
        """Return a schema response for a question about the given date.

        Stages, in order: language, intent, context and clarification,
        retrieval, evidence validation, rules, grounded generation.
        Verification and escalation are added in phase 10.
        """
        trace = {"language_detected": detect_language(question)}
        language = answer_language(question)
        intent = self.classifier.classify(question)
        trace["intent"] = intent
        if intent == "OUT_OF_SCOPE":
            return {**non_answer("OUT_OF_SCOPE", intent, language, as_of), "_trace": trace}
        context = extract_context(question, intent)
        trace["context"] = context
        if context["missing"]:
            return {**non_answer("CLARIFICATION_REQUIRED", intent, language, as_of,
                                 missing=context["missing"]), "_trace": trace}
        chunks = self.retriever.search(question, as_of, "hybrid", self.top_k)
        trace["retrieved"] = [c["chunk_id"] for c in chunks]
        report = validate_evidence(intent, question, chunks, self.sources_by_id, as_of)
        trace["evidence_status"] = report["status"]
        trace["off_topic"] = [o["chunk_id"] for o in report["off_topic"]]
        trace["overridden"] = report["overridden_chunks"]
        if report["status"] != "OK":
            unresolved = [c for c in report["conflicts"] if c["winner"] is None]
            return {**non_answer(report["status"], intent, language, as_of, conflicts=unresolved), "_trace": trace}
        rules = run_rules(self.engine, intent, question, context, as_of)
        trace["rules"] = [(r["rule_id"], r["output"]) for r in rules]
        response = self.generator.answer(question, intent, language, as_of,
                                         report["evidence"], rules, report["conditions"])
        return {**response, "_trace": trace}
