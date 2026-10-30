"""Extract stated facts from a question without inventing anything."""
from app.documents.normalize import normalize_for_search
from app.intent.taxonomy import REQUIRED_CONTEXT

PATTERNS = {
    "degree_level": [
        ("phd", ["دكتوراه", "دكتوراة", "الدكتوراه", "phd", "doctor"]),
        ("master", ["ماجستير", "ماجيستير", "الماجستير", "master"]),
        ("diploma", ["دبلوم", "الدبلوم", "diploma"]),
    ],
    "term": [
        ("T1", ["الفصل الاول", "الفصل الدراسي الاول", "الترم الاول", "first semester",
                "first term", "fall semester", "semester 1", "term 1"]),
        ("T2", ["الفصل الثاني", "الفصل الدراسي الثاني", "الترم الثاني", "second semester",
                "second term", "spring semester", "semester 2", "term 2"]),
    ],
    "withdrawal_scope": [
        ("course", ["ماده", "مقرر", "course", "class", "subject"]),
        ("semester", ["الفصل", "الترم", "semester", "term"]),
        ("program", ["البرنامج", "الجامعه", "program", "university"]),
    ],
}


def extract_context(question, intent):
    """Return the context values stated in a question and the ones still missing.

    Only values written in the question are returned. Nothing is filled with a
    plausible default; anything the intent needs but the question omits goes in
    the missing list.

    Args:
        question: the student question.
        intent: the classified intent.

    Returns:
        A dict with "values" (field -> value) and "missing" (list of fields).
    """
    text = normalize_for_search(question)
    values = {}
    for field, options in PATTERNS.items():
        for value, keywords in options:
            if any(k in text for k in keywords):
                values[field] = value
                break
    missing = [f for f in REQUIRED_CONTEXT.get(intent, []) if f not in values]
    return {"values": values, "missing": missing}
