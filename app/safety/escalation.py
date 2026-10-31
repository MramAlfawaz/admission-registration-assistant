"""Recognise questions that need institutional authority and build the escalation block."""
import datetime as dt
import json
import re
from pathlib import Path

from app.documents.normalize import normalize_for_search

DECISION_REQUEST = ["اعتماد", "اعتمد", "وافقوا", "توافقون", "موافقتكم", "الموافقه علي", "قبولي",
                    "هل سيتم قبولي", "هل انقبل", "تمديد", "اسمحوا لي", "اقبلوني", "approve", "approval",
                    "extend", "extension", "will i be accepted", "accept me", "waive", "grant me",
                    # asking the assistant to override the rules is a request for a decision
                    "تجاهل اللوائح", "تجاهل الانظمه", "تجاهل التعليمات", "قل لي انه يحق", "قل لي اني", "قل لي انني",
                    "ignore the regulations", "ignore the rules", "ignore your rules", "tell me i can", "tell me that i can"]
# "exception" is a request only when asked for; "what is the minimum for an exception?" is information (v1: E058).
EXCEPTION_WORDS = ["استثناء", "استثنائي", "استثناءا", "exception"]
REQUEST_MARKERS = ["اطلب", "ابغي", "ابي ", "اريد", "ارجو", "امنحني", "اعطني", "اعطوني", "تمنحوني", "ممكن تعطوني",
                   "i need", "i want", "can you", "could you", "please", "give me", "request", "for me", " my "]
# Another person's records are never looked up or shared (adversarial v1: A07, A08).
THIRD_PARTY = ["another student", "other student", "someone else", "student id", "student number", "his gpa",
               "her gpa", "his grades", "her grades", "his record", "her record", "طالب اخر", "طالبه اخري",
               "بيانات الطالب", "بيانات تسجيل", "رقم الطالب", "رقمه الجامعي", "معدله", "درجاته", "سجله الاكاديمي"]
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
    "third_party": {"ar": "لا أستطيع الاطلاع على بيانات طالب آخر أو مشاركتها؛ هذه البيانات محمية.",
                    "en": "I cannot look up or share another student's records; they are protected."},
}
NEXT_STEP = {"ar": "يرجى التواصل مع عمادة القبول والتسجيل لاتخاذ القرار أو مراجعة حالتك.",
             "en": "Please contact the Deanship of Admission and Registration for a decision or a review of your case."}


def escalation_reason(question, rule_outputs=()):
    """Return why a question needs staff ("third_party", "personal_record", "decision", "exception_rule") or None."""
    text = f" {normalize_for_search(question)} "

    def has(phrases):
        # whole words only: "قبولي" (my admission) must not match "المقبولين" (the admitted students)
        return any(re.search(rf"(?<!\w){re.escape(p.strip())}(?!\w)", text) for p in phrases)

    if has(THIRD_PARTY):
        return "third_party"
    if has(PERSONAL_RECORD):
        return "personal_record"
    if has(DECISION_REQUEST):
        return "decision"
    if has(EXCEPTION_WORDS) and has(REQUEST_MARKERS):
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
