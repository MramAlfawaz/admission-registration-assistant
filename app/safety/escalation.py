"""Recognise questions that need institutional authority and build the escalation block."""
import datetime as dt
import json
from pathlib import Path

from app.documents.normalize import normalize_for_search

DECISION_REQUEST = ["استثناء", "استثنائي", "اعتماد", "وافقوا", "توافقون", "موافقتكم", "الموافقه علي", "قبولي",
                    "هل سيتم قبولي", "هل انقبل", "تمديد", "اسمحوا لي", "اقبلوني", "approve", "approval",
                    "exception", "extend", "extension", "will i be accepted", "accept me", "waive", "grant me"]
PERSONAL_RECORD = ["كم معدلي", "معدلي كم", "درجاتي", "سجلي", "سجلي الاكاديمي", "what is my gpa", "my grades",
                   "my record", "my transcript"]
EXCEPTION_OUTPUTS = {"deprived_exception_possible", "exception_only"}
REASONS = {
    "decision": {"ar": "يتعلق هذا الطلب بقرار رسمي أو استثناء من الجهة المختصة، ولا يمكنني اتخاذ هذا القرار أو توقعه.",
                 "en": "This request concerns an official decision or an exception, which I cannot make or predict."},
    "exception_rule": {"ar": "تسمح اللائحة بذلك على سبيل الاستثناء فقط، ويعود القرار إلى المجالس المختصة.",
                       "en": "The regulation allows this only as an exception decided by the responsible councils."},
    "personal_record": {"ar": "يحتاج هذا السؤال إلى سجلك الأكاديمي الشخصي، ولا أستطيع الاطلاع عليه.",
                        "en": "This question needs your personal academic record, which I cannot access."},
}
NEXT_STEP = {"ar": "يرجى التواصل مع عمادة القبول والتسجيل لاتخاذ القرار أو مراجعة حالتك.",
             "en": "Please contact the Deanship of Admission and Registration for a decision or a review of your case."}


def escalation_reason(question, rule_outputs=()):
    """Return why a question needs staff ("decision", "personal_record", "exception_rule") or None."""
    text = normalize_for_search(question)
    if any(p in text for p in PERSONAL_RECORD):
        return "personal_record"
    if any(p in text for p in DECISION_REQUEST):
        return "decision"
    if any(r["output"] in EXCEPTION_OUTPUTS for r in rule_outputs):
        return "exception_rule"
    return None


def escalation_block(reason, language, confirmed, sources):
    """Build the block the brief describes: reason, what can be confirmed, evidence, next step."""
    return {"reason": REASONS[reason][language], "reason_code": reason, "confirmed": confirmed,
            "evidence": [{"source_id": s["source_id"], "section": s.get("section") or s.get("chunk_id")} for s in sources],
            "next_step": NEXT_STEP[language]}


def record_escalation(path, reason, intent, sources, as_of):
    """Append an escalation record without the question text (docs/data-handling.md)."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    entry = {"logged_at": dt.datetime.now().isoformat(timespec="seconds"), "as_of": str(as_of),
             "reason": reason, "intent": intent, "sources": sorted({s["source_id"] for s in sources})}
    with Path(path).open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
