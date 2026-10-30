"""Drop evidence that is about a different situation than the one asked."""
from app.documents.normalize import normalize_for_search

# A chunk must contain at least one anchor (search form) to support the intent.
# Intents without an entry are not filtered.
ANCHORS = {
    "SEMESTER_WITHDRAWAL": ["اعتذار", "معتذر", "اعتذر"],
    "POSTPONEMENT": ["تاجيل", "اجل "],
    "PROGRAM_WITHDRAWAL": ["انسحاب", "انسحب"],
    "COURSE_WITHDRAWAL": ["حذف ماده", "حذف مقرر", "الحذف والاضافه", "حذف واضافه"],
    "REENROLLMENT": ["اعاده القيد", "اعاده قيد", "طي القيد", "مطوي"],
    "ATTENDANCE": ["حضور", "حرمان", "يحرم", "غياب"],
    "FEES": ["رسوم", "ريال", "استرداد", "تسترد"],
    "STUDY_DURATION": ["مده", "سنوات", "عامان", "فصول", "فصلان", "الحد الاقصي"],
    "GRADUATION_REQUIREMENTS": ["تخرج", "الشامل", "مرتبه الشرف", "الرساله", "معدل"],
    "GRADING_AND_STANDING": ["درجه", "تقدير", "معدل", "انذار", "رسوب", "تظلم", "اجتياز", "طي القيد"],
    "ACADEMIC_CALENDAR": ["بدايه الدراسه", "اجازه", "الاختبارات", "عوده", "يوم"],
}


def filter_relevant(chunks, intent):
    """Split chunks into those about the asked situation and those that are not.

    Example: for SEMESTER_WITHDRAWAL, a passage about refunds after program
    withdrawal has no withdrawal-from-semester anchor and is set aside.

    Args:
        chunks: chunk dictionaries in force on the query date.
        intent: the classified intent.

    Returns:
        A (relevant, off_topic) pair; off-topic items carry a reason.
    """
    anchors = ANCHORS.get(intent)
    if not anchors:
        return list(chunks), []
    relevant, off_topic = [], []
    for c in chunks:
        text = normalize_for_search(f"{c.get('section') or ''} {c['text']}")
        if any(a in text for a in anchors):
            relevant.append(c)
        else:
            off_topic.append({"chunk_id": c["chunk_id"], "reason": f"no {intent} anchor"})
    return relevant, off_topic
