"""Baseline intent classifier: weighted keyword rules.

Keywords are written in the search form produced by normalize_for_search
(alef variants unified, taa marbuta as haa, alef maqsura as yaa, lowercase).
Specific phrases carry weight 3, general words weight 1.
"""
from app.documents.normalize import normalize_for_search

RULES = {
    "SEMESTER_WITHDRAWAL": [
        ("اعتذار عن الفصل", 3), ("الاعتذار عن الدراسه", 3), ("اعتذر عن الفصل", 3),
        ("انسحب من الفصل", 3), ("الانسحاب من الفصل", 3), ("اعتذار", 2), ("اعتذر", 2),
        ("withdraw from the semester", 3), ("semester withdrawal", 3),
        ("withdraw from this semester", 3), ("drop the whole semester", 3),
        ("drop the semester", 3), ("withdraw from the term", 3),
    ],
    "POSTPONEMENT": [
        ("تاجيل الفصل", 3), ("اجل الفصل", 3), ("اجل دراستي", 3), ("تاجيل الدراسه", 3),
        ("تاجيل", 2), ("اجل", 1), ("postpone", 3), ("defer the semester", 3),
        ("defer my studies", 3), ("defer this semester", 3), ("defer", 1),
    ],
    "PROGRAM_WITHDRAWAL": [
        ("انسحاب من البرنامج", 3), ("الانسحاب من البرنامج", 3), ("انسحب من البرنامج", 3),
        ("الانسحاب من الجامعه", 3), ("انسحب من الجامعه", 3), ("اترك الجامعه", 3),
        ("اطلع من الجامعه", 3), ("withdraw from the program", 3),
        ("withdraw from the university", 3), ("leave the program", 3),
        ("quit the program", 3), ("leave the university", 3),
    ],
    "COURSE_WITHDRAWAL": [
        ("حذف ماده", 3), ("احذف ماده", 3), ("احذف الماده", 3), ("اسحب الماده", 3),
        ("اسحب ماده", 3), ("انسحب من ماده", 3), ("انسحب من الماده", 3), ("حذف واضافه", 3),
        ("الحذف والاضافه", 3), ("مقرر واحد", 2), ("drop a course", 3), ("drop the course", 3),
        ("drop one course", 3), ("withdraw from a course", 3), ("add and drop", 3),
        ("add/drop", 3), ("course withdrawal", 3), ("drop a class", 3),
    ],
    "WITHDRAWAL_UNSPECIFIED": [
        ("انسحب", 1), ("اسحب", 1), ("انسحاب", 1), ("withdraw", 1), ("withdrawal", 1),
    ],
    "REENROLLMENT": [
        ("اعاده القيد", 3), ("اعاده قيد", 3), ("طي القيد", 3), ("قيدي مطوي", 3),
        ("re-enrol", 3), ("reenrol", 3), ("re-enroll", 3), ("readmission", 3),
        ("reinstat", 3), ("enrolment was closed", 3), ("enrollment was closed", 3),
    ],
    "ACADEMIC_CALENDAR": [
        ("التقويم", 3), ("تبدا الدراسه", 3), ("بدايه الدراسه", 3), ("الاختبارات النهائيه", 3),
        ("اختبارات نهائيه", 3), ("اجازه", 2), ("عيد", 2), ("اليوم الوطني", 3), ("يوم التاسيس", 3),
        ("الدوام", 1), ("calendar", 3), ("semester start", 3), ("classes start", 3),
        ("final exam", 3), ("holiday", 2), ("break", 1), ("semester begin", 3),
        ("study start", 3), ("start date", 2),
    ],
    "ATTENDANCE": [
        ("حضور", 3), ("الحضور", 3), ("غياب", 3), ("غيابي", 3), ("الحرمان", 3), ("محروم", 3),
        ("حرمان", 3), ("attendance", 3), ("absence", 3), ("absent", 3), ("barred", 3),
        ("miss classes", 3), ("skip classes", 2),
    ],
    "GRADING_AND_STANDING": [
        ("المعدل التراكمي", 2), ("معدلي", 2), ("انذار", 3), ("انذارات", 3), ("درجه النجاح", 3),
        ("رسوب", 3), ("رسبت", 3), ("اعتراض", 3), ("تظلم", 3), ("سلم الدرجات", 3), ("الدرجات", 1),
        ("gpa", 2), ("grade", 2), ("warning", 3), ("probation", 3), ("fail", 2), ("appeal", 3),
        ("passing mark", 3), ("pass mark", 3), ("dismiss", 2),
    ],
    "GRADUATION_REQUIREMENTS": [
        ("تخرج", 3), ("التخرج", 3), ("اتخرج", 3), ("الاختبار الشامل", 3), ("رساله الماجستير", 2),
        ("الرساله", 1), ("مرتبه الشرف", 3), ("graduat", 3), ("comprehensive exam", 3),
        ("thesis", 2), ("honours", 3), ("honors", 3),
    ],
    "ADMISSION_REQUIREMENTS": [
        ("شروط القبول", 3), ("متطلبات القبول", 3), ("شروط", 2), ("يشترط", 2), ("ايلتس", 3),
        ("ielts", 3), ("اللغه الانجليزيه", 2), ("خبره", 2), ("التقدير المطلوب", 3),
        ("تقدير مقبول", 3), ("بتقدير", 2), ("اقدر اقدم", 2), ("يحق لي التقديم", 2),
        ("مقبول", 1), ("requirement", 3), ("eligib", 3), ("qualif", 2), ("minimum grade", 3),
        ("english test", 3), ("can i apply", 2), ("accepted", 1), ("criteria", 3),
    ],
    "ADMISSION_DOCUMENTS": [
        ("الوثائق", 3), ("وثائق", 3), ("المستندات", 3), ("مستندات", 3), ("الاوراق", 3),
        ("اوراق", 3), ("جواز", 2), ("صور شخصيه", 3), ("صورتين", 2), ("السجل الاكاديمي", 3),
        ("documents", 3), ("papers", 3), ("passport", 2), ("transcript", 3), ("photos", 2),
        ("bring", 1),
    ],
    "ADMISSION_PROCEDURE": [
        ("كيف اقدم", 3), ("طريقه التقديم", 3), ("خطوات التقديم", 3), ("التقديم", 2),
        ("اقدم", 1), ("بوابه القبول", 3), ("مقابله", 3), ("المقابله", 3), ("المفاضله", 3),
        ("نتيجه القبول", 3), ("نتائج القبول", 3), ("تاجيل القبول", 4), ("رغبه", 3),
        ("رغبات", 3), ("موعد القبول", 3), ("مره ثانيه", 2), ("مره اخري", 2),
        ("how to apply", 3), ("how do i apply", 3), ("application", 2), ("apply", 1),
        ("portal", 3), ("interview", 3), ("admission result", 3), ("apply again", 3),
        ("defer my admission", 4), ("defer admission", 4), ("more than one program", 3),
        ("admission open", 3),
    ],
    "FEES": [
        ("رسوم", 3), ("الرسوم", 3), ("تكلفه", 3), ("سعر", 2), ("ريال", 2), ("استرداد", 3),
        ("تقسيط", 3), ("اقساط", 3), ("كم يكلف", 3), ("fee", 3), ("tuition", 3), ("cost", 3),
        ("refund", 3), ("pay", 2), ("installment", 3), ("how much", 2), ("price", 3),
    ],
    "STUDY_DURATION": [
        ("مده الدراسه", 3), ("كم سنه", 3), ("كم مده", 3), ("كم فصل", 3), ("الحد الاقصي", 3),
        ("مده البرنامج", 3), ("duration", 3), ("how long", 3), ("how many years", 3),
        ("how many semesters", 3), ("maximum period", 3), ("maximum duration", 3),
    ],
    "PROGRAM_INFORMATION": [
        ("البرامج", 2), ("برنامج", 1), ("تخصص", 2), ("تخصصات", 2), ("مسائي", 3), ("صباحي", 3),
        ("مسائيه", 3), ("لغه الدراسه", 3), ("بالانجليزي", 2), ("programs", 2), ("program", 1),
        ("majors", 2), ("evening", 3), ("taught in", 3), ("offered", 2),
    ],
    "OUT_OF_SCOPE": [
        ("سكن", 4), ("فندق", 4), ("واي فاي", 4), ("wifi", 4), ("البريد الجامعي", 4),
        ("الايميل الجامعي", 4), ("كلمه المرور", 4), ("باسورد", 4), ("شكوي", 4), ("اشتكي", 4),
        ("مواقف", 4), ("كافتيريا", 4), ("منحه", 4), ("منح", 3), ("مكافاه", 4), ("راتب", 4),
        ("housing", 4), ("dorm", 4), ("hotel", 4), ("password", 4), ("email account", 4),
        ("complaint", 4), ("parking", 4), ("cafeteria", 4), ("scholarship", 4), ("salary", 4),
        ("library", 3), ("المكتبه", 3), ("weather", 4), ("الطقس", 4),
    ],
}

PRIORITY = list(RULES)


def classify(question):
    """Return the intent with the highest keyword score.

    Ties go to the intent listed first in RULES (more specific intents come
    first). A question with no matching keyword is OUT_OF_SCOPE.

    Args:
        question: the student question in Arabic or English.

    Returns:
        An intent label from the taxonomy.
    """
    text = normalize_for_search(question)
    scores = {intent: sum(w for kw, w in rules if kw in text) for intent, rules in RULES.items()}
    best = max(PRIORITY, key=lambda i: (scores[i], -PRIORITY.index(i)))
    return best if scores[best] > 0 else "OUT_OF_SCOPE"
