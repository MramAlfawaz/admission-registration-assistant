"""Detect when an answer depends on information the question does not state (Stage 3).

Ambiguity is read from the question text itself, so a misclassified intent cannot
trigger a pointless question, and a clear question is never interrupted.
"""
from app.documents.normalize import normalize_for_search

GENERIC_WITHDRAWAL = ["انسحب", "انسحاب", "اسحب", "انسحبت", "withdraw", "drop out", "quit"]
SCOPE_WORDS = {
    "course": ["ماده", "مقرر", "course", "class", "subject"],
    "semester": ["الفصل", "الترم", "فصل", "semester", "term", "اعتذار", "اعتذر"],
    "program": ["البرنامج", "الجامعه", "program", "university", "نهائيا"],
}
DEGREE_WORDS = ["دكتوراه", "دكتوراة", "ماجستير", "ماجيستير", "دبلوم", "phd", "doctor", "master", "diploma"]
PROGRAM_WORDS = ["علم الجريمه", "الامن الوطني", "السيبرانيه", "الذكاء الاصطناعي", "الاقتصاديه", "انفاذ القانون",
                 "الادله الجنائيه", "حقوق الانسان", "الارهاب", "الحدود", "المخدرات", "القانون الجنائي",
                 "criminology", "security", "cyber", "ai", "economic", "law enforcement", "forensic",
                 "human rights", "terrorism", "border", "drug", "criminal law"]
DURATION_OR_GRADUATION = ["مده", "كم سنه", "كم فصل", "تخرج", "اتخرج", "how long", "duration", "years", "graduat"]
SCOPE_TO_INTENT = {"course": "COURSE_WITHDRAWAL", "semester": "SEMESTER_WITHDRAWAL", "program": "PROGRAM_WITHDRAWAL"}


def detect_missing(question, intent, supplied=None):
    """Return the one piece of missing information to ask about, or None.

    Args:
        question: the student question.
        intent: the classified intent.
        supplied: values already given in a clarification reply.
    """
    supplied = supplied or {}
    text = f" {normalize_for_search(question)} "
    if "withdrawal_scope" not in supplied and any(w in text for w in GENERIC_WITHDRAWAL):
        if not any(w in text for words in SCOPE_WORDS.values() for w in words):
            return "withdrawal_scope"
    if ("degree_level" not in supplied and intent in ("STUDY_DURATION", "GRADUATION_REQUIREMENTS")
            and any(w in text for w in DURATION_OR_GRADUATION)
            and not any(w in text for w in DEGREE_WORDS)
            and not any(f" {w} " in text or w in text for w in PROGRAM_WORDS if len(w) > 3)):
        return "degree_level"
    return None


def apply_clarification(intent, supplied):
    """Return the intent after a clarification reply (for example semester -> SEMESTER_WITHDRAWAL)."""
    return SCOPE_TO_INTENT.get(supplied.get("withdrawal_scope"), intent)


DEGREE_QUERY = {"phd": "الدكتوراه", "master": "الماجستير", "diploma": "الدبلوم العالي"}
SCOPE_QUERY = {"course": "حذف مادة", "semester": "الاعتذار عن الفصل الدراسي", "program": "الانسحاب من البرنامج"}


def clarified_query(question, supplied):
    """Append the clarified values to the search query so retrieval uses them."""
    extra = [DEGREE_QUERY.get(supplied.get("degree_level"), ""), SCOPE_QUERY.get(supplied.get("withdrawal_scope"), "")]
    return " ".join([question] + [e for e in extra if e])
