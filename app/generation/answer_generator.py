"""Build responses: fixed templates for non-answers, the local model for answers."""
import json
import logging

from app.generation.templates import CLARIFY, CLARIFY_OPTIONS, CONTACT, DATE_BASIS, OUT_OF_SCOPE_ACTION, TEXTS
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
        r["clarification"] = {"missing": field, "question": CLARIFY[field][language],
                              "options": [{"value": v, "label": lab[language]} for v, lab in CLARIFY_OPTIONS[field]]}
        return r
    r["answer"] = TEXTS[status][language]
    r["required_action"] = OUT_OF_SCOPE_ACTION[language] if status == "OUT_OF_SCOPE" else CONTACT[language]
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

    def __init__(self, client, prompts_dir="prompts", evidence_limit=3, evidence_chars=700, prompt_name="answer_v2"):
        self.client = client
        self.prompt_name = prompt_name
        self.header, self.template = load_prompt(prompt_name, prompts_dir)
        _, self.glossary = load_prompt("glossary_v1", prompts_dir)
        self.evidence_limit, self.evidence_chars = evidence_limit, evidence_chars

    def draft(self, question, language, as_of, evidence, rule_outputs, rule_texts):
        """Ask the model for an explanation to add after the fixed rule sentences.

        Returns:
            A dict with explanation, conditions, required_action, the passages
            given and the passages the model says it used. Raises ValueError
            when the model output is not valid JSON.
        """
        given = evidence[: self.evidence_limit]
        labelled = {f"E{i}": c for i, c in enumerate(given, 1)}
        evidence_text = "\n\n".join(
            f"[{label}] (page {c.get('page')}, {c.get('section') or ''}):\n"
            f"{' '.join(c['text'].split())[: self.evidence_chars]}"
            for label, c in labelled.items())
        stated = "\n".join(f"- {t}" for t in rule_texts) or "(nothing)"
        prompt = fill(self.template, language_name=LANGUAGE_NAMES[language], glossary=self.glossary,
                      as_of=as_of, question=question, stated=stated, rules=_rules_text(rule_outputs),
                      evidence=evidence_text)
        output = self.client.generate_json(prompt)
        used = [labelled[e] for e in output.get("used_evidence", []) if e in labelled] or given
        return {"explanation": str(output.get("answer", "")).strip(),
                "conditions": [str(c).strip() for c in output.get("conditions", []) if str(c).strip()]
                if isinstance(output.get("conditions"), list) else [],
                "required_action": str(output.get("required_action", "")).strip()
                if not isinstance(output.get("required_action"), list)
                else " ".join(str(x) for x in output["required_action"]),
                "given": given, "used": used}
