"""Fixed sentences for rule results: dates, open/closed and thresholds are never left to the model."""
import datetime as dt

from app.documents.normalize import normalize_for_search

WEEKDAYS = {"ar": ["الإثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت", "الأحد"],
            "en": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]}
TERMS = {"ar": {"T1": "الفصل الدراسي الأول", "T2": "الفصل الدراسي الثاني"},
         "en": {"T1": "first semester", "T2": "second semester"}}
RESOLVED = {"ar": " (حُدد الفصل بحسب تاريخ السؤال)", "en": " (term identified from the question date)"}

CALENDAR = {
    "RULE-CAL-01": {
        "ar": ("آخر موعد للاعتذار عن {term} هو {when}، وفترة الاعتذار ما زالت مفتوحة حتى ذلك التاريخ.",
               "آخر موعد للاعتذار عن {term} كان {when}، وقد انتهت فترة الاعتذار عن هذا الفصل."),
        "en": ("The deadline to withdraw from the {term} is {when}; the withdrawal period is still open until then.",
               "The deadline to withdraw from the {term} was {when}; this withdrawal period has closed.")},
    "RULE-CAL-02": {
        "ar": ("آخر موعد لتأجيل {term} هو {when}، وفترة التأجيل ما زالت مفتوحة حتى ذلك التاريخ.",
               "آخر موعد لتأجيل {term} كان {when}، وقد انتهت فترة التأجيل لهذا الفصل."),
        "en": ("The deadline to postpone the {term} is {when}; the postponement period is still open until then.",
               "The deadline to postpone the {term} was {when}; this postponement period has closed.")},
    "RULE-CAL-03": {
        "ar": ("آخر موعد لطلب إعادة القيد في {term} هو {when}، والفترة ما زالت مفتوحة حتى ذلك التاريخ.",
               "آخر موعد لطلب إعادة القيد في {term} كان {when}، وقد انتهت هذه الفترة."),
        "en": ("The deadline to request re-enrolment for the {term} is {when}; the period is still open until then.",
               "The deadline to request re-enrolment for the {term} was {when}; this period has closed.")},
    "RULE-CAL-04": {
        "ar": ("تبدأ الدراسة في {term} يوم {when}؛ الانسحاب قبل هذا التاريخ يتيح استرداد الرسوم الدراسية لهذا الفصل فقط، ولا تسترد الرسوم الإدارية.",
               "بدأت الدراسة في {term} يوم {when}، ولا تسترد الرسوم الدراسية المدفوعة لهذا الفصل عند الانسحاب بعد بدء الدراسة."),
        "en": ("Study in the {term} starts on {when}; withdrawing before that date allows a refund of that term's tuition only, and administrative fees are not refunded.",
               "Study in the {term} started on {when}; tuition already paid for that term is not refunded on withdrawal after study starts.")},
    "RULE-CAL-05": {
        "ar": ("يمكن تقديم طلب الانسحاب من البرنامج قبل بدء الاختبارات النهائية في {term} يوم {when}.",
               "بدأت الاختبارات النهائية في {term} يوم {when}، وانتهت فترة تقديم طلب الانسحاب من البرنامج لهذا الفصل."),
        "en": ("A request to withdraw from the program can be submitted before final exams of the {term} start on {when}.",
               "Final exams of the {term} started on {when}; the period to request withdrawal from the program for that term has closed.")},
}
THRESHOLDS = {
    ("RULE-REG-01", "eligible_for_final"): {
        "ar": "نسبة حضور {value}% تحقق الحد الأدنى المطلوب لدخول الاختبار النهائي وهو 75%.",
        "en": "An attendance of {value}% meets the 75% minimum required to sit the final exam."},
    ("RULE-REG-01", "deprived_exception_possible"): {
        "ar": "نسبة حضور {value}% أقل من 75%، فيُحرم الطالب من دخول الاختبار النهائي، ويجوز رفع الحرمان استثناءً فقط بعذر يقبله مجلسا القسم والكلية وبنسبة حضور لا تقل عن 50%.",
        "en": "An attendance of {value}% is below 75%, so the student is barred from the final exam; the bar can be lifted only as an exception, with an excuse accepted by the department and college councils and attendance of at least 50%."},
    ("RULE-REG-01", "deprived"): {
        "ar": "نسبة حضور {value}% أقل من 50%، فيُحرم الطالب من دخول الاختبار النهائي ولا ينطبق عليه استثناء رفع الحرمان.",
        "en": "An attendance of {value}% is below 50%, so the student is barred from the final exam and the exception does not apply."},
    ("RULE-REG-02", "passed"): {"ar": "درجة {value} تحقق درجة النجاح في المقرر وهي 70 من 100.",
                                "en": "A grade of {value} meets the course pass mark of 70 out of 100."},
    ("RULE-REG-02", "failed"): {"ar": "درجة {value} أقل من درجة النجاح في المقرر وهي 70 من 100.",
                                "en": "A grade of {value} is below the course pass mark of 70 out of 100."},
    ("RULE-REG-03", "warning"): {"ar": "معدل تراكمي {value} أقل من {threshold} من 5، وهو الحد الذي يوجه دونه إنذار أكاديمي.",
                                 "en": "A cumulative GPA of {value} is below {threshold} out of 5, the level under which an academic warning is issued."},
    ("RULE-REG-03", "no_warning"): {"ar": "معدل تراكمي {value} لا يقل عن {threshold} من 5، فلا يستوجب إنذاراً أكاديمياً.",
                                    "en": "A cumulative GPA of {value} is not below {threshold} out of 5, so it does not lead to an academic warning."},
    ("RULE-ELIG-01", "meets_gpa"): {"ar": "معدل تراكمي {value} يحقق المعدل المطلوب للتخرج وهو {threshold} من 5.",
                                    "en": "A cumulative GPA of {value} meets the graduation requirement of {threshold} out of 5."},
    ("RULE-ELIG-01", "below_gpa"): {"ar": "معدل تراكمي {value} أقل من المعدل المطلوب للتخرج وهو {threshold} من 5.",
                                    "en": "A cumulative GPA of {value} is below the graduation requirement of {threshold} out of 5."},
}
VALUE_INPUT = {"RULE-REG-01": "attendance_percent", "RULE-REG-02": "course_grade",
               "RULE-REG-03": "gpa", "RULE-ELIG-01": "gpa"}


def _when(details, language):
    """Return 'weekday YYYY-MM-DD (hijri AH)' for a calendar rule result."""
    day = dt.date.fromisoformat(details["date"])
    hijri = f"{details['hijri']}هـ" if language == "ar" else f"{details['hijri']} AH"
    return f"{WEEKDAYS[language][day.weekday()]} {details['date']} ({hijri})"


def _number(value):
    return f"{value:g}" if isinstance(value, float) else str(value)


def rule_sentence(result, language, inputs=None):
    """Return the fixed sentence for one rule result, or None when it has none.

    Args:
        result: a rule engine result.
        language: "ar" or "en".
        inputs: the rule inputs the student stated (for threshold rules).
    """
    rule_id, output, details = result["rule_id"], result["output"], result["details"]
    if rule_id in CALENDAR and output in ("open", "closed", "refund_eligible", "refund_not_eligible"):
        first = output in ("open", "refund_eligible")
        term = TERMS[language][details["term_id"].split("-")[-1]]
        text = CALENDAR[rule_id][language][0 if first else 1].format(term=term, when=_when(details, language))
        if details.get("term_basis", "").endswith("resolved from as_of"):
            text = text[:-1] + RESOLVED[language] + text[-1]
        return text
    template = THRESHOLDS.get((rule_id, output))
    if template:
        value = (inputs or {}).get(VALUE_INPUT[rule_id], "")
        return template[language].format(value=_number(value), threshold=_number(details.get("threshold", "")))
    return None


# ---- calendar rows looked up by code (CAL-EVENT) ----

def _day(date, language):
    return WEEKDAYS[language][dt.date.fromisoformat(date).weekday()]


def event_sentence(details, language):
    """Fixed sentence for a calendar row: event name, weekday(s), Gregorian and Hijri dates."""
    end_of_day = "نهايه دوام" in normalize_for_search(details.get("day", ""))
    one_day = details["date"] == details["date_end"]
    if language == "ar":
        when = (f"{_day(details['date'], 'ar')} {details['date']} ({details['hijri']}هـ)" if one_day else
                f"من {_day(details['date'], 'ar')} {details['date']} إلى {_day(details['date_end'], 'ar')} "
                f"{details['date_end']} ({details['hijri']} إلى {details['hijri_end']}هـ)")
        return f"{details['event']} حسب التقويم الأكاديمي: {'نهاية دوام ' if end_of_day else ''}{when}."
    when = (f"{_day(details['date'], 'en')} {details['date']} ({details['hijri']} AH)" if one_day else
            f"{_day(details['date'], 'en')} {details['date']} to {_day(details['date_end'], 'en')} "
            f"{details['date_end']} ({details['hijri']} to {details['hijri_end']} AH)")
    return (f"The academic calendar lists “{details['event']}” on {when}"
            f"{', at the end of the working day' if end_of_day else ''}.")


# ---- thresholds stated by code when a student asks what the rule is ----
# Each entry: rule whose numbers are stated, question triggers (search form), and the sentence.
STATEMENTS = [
    ("RULE-REG-02", ["درجه النجاح", "اجتياز المقرر", "انجح", "pass mark", "passing mark", "passing grade", "to pass"],
     {"ar": "درجة النجاح في المقرر الدراسي 70 من 100 كحد أدنى.",
      "en": "The pass mark for a course is 70 out of 100."}),
    ("RULE-ELIG-02", ["مرتبه الشرف", "مراتب الشرف", "honours", "honors"],
     {"ar": "تمنح مرتبة الشرف الأولى لمعدل تراكمي 4.75 من 5 فأعلى، والثانية لمعدل من 4.50 إلى أقل من 4.75، "
            "بشرط ألا يكون الطالب قد رسب في أي مقرر أو صدر بحقه جزاء تأديبي أو طوي قيده.",
      "en": "First honours requires a cumulative GPA of 4.75 out of 5 or more, and second honours 4.50 to under 4.75, "
            "provided the student never failed a course, received no disciplinary penalty and was never closed out of enrolment."}),
    ("RULE-REG-01", ["نسبه الحضور", "الحضور", "حضور", "احضر", "attendance"],
     {"ar": "الحد الأدنى للحضور لدخول الاختبار النهائي 75% من المحاضرات، ويجوز استثناءً رفع الحرمان بعذر يقبله "
            "مجلسا القسم والكلية بشرط ألا تقل نسبة الحضور عن 50%.",
      "en": "The minimum attendance to sit the final exam is 75% of lectures; the bar can be lifted only as an exception, "
            "with an excuse accepted by the department and college councils and attendance of at least 50%."}),
]
# Rules whose number depends on the degree; both values are stated when the degree is not named.
STATEMENTS.append(
    ("RULE-REG-04", ["انذارين", "two consecutive", "two warnings", "two academic warnings", "second warning"],
     {"ar": "يطوى قيد الطالب إذا حصل على إنذارين أكاديميين متتاليين.",
      "en": "A student's enrolment is closed after two consecutive academic warnings."}))
BY_DEGREE = {
    "RULE-REG-03": (["انذار", "warning"],
                    {"ar": ("يوجه الإنذار الأكاديمي إذا انخفض المعدل التراكمي عن {phd} من 5 في الدكتوراه والماجستير، "
                            "وعن {diploma} من 5 في الدبلوم العالي."),
                     "en": ("An academic warning is issued when the cumulative GPA falls below {phd} out of 5 for PhD and "
                            "master's students, and below {diploma} out of 5 for higher diploma students.")}),
    "RULE-ELIG-01": (["تخرج", "اتخرج", "graduat"],
                     {"ar": ("المعدل التراكمي المطلوب للتخرج {phd} من 5 للدكتوراه والماجستير، و{diploma} من 5 للدبلوم العالي."),
                      "en": ("Graduation requires a cumulative GPA of at least {phd} out of 5 for PhD and master's students, "
                             "and {diploma} out of 5 for higher diploma students.")}),
    "RULE-REG-06": (["تظلم", "appeal"],
                    {"ar": ("يحق لطالب الدكتوراه أو الماجستير التظلم من درجة الاختبار النهائي {phd} مرات خلال دراسته، "
                            "ولطالب الدبلوم العالي مرتين، ويقدم التظلم خلال ثلاثة أيام من إعلان النتيجة."),
                     "en": ("PhD and master's students may appeal a final exam grade {phd} times during their studies and "
                            "higher diploma students twice; an appeal is submitted within three days of the result.")}),
}
DEGREE_ONLY = {
    "RULE-REG-03": {"ar": "يوجه الإنذار الأكاديمي إذا انخفض المعدل التراكمي عن {value} من 5 في {degree}.",
                    "en": "An academic warning is issued when the cumulative GPA falls below {value} out of 5 for {degree} students."},
    "RULE-ELIG-01": {"ar": "المعدل التراكمي المطلوب للتخرج في {degree} {value} من 5.",
                     "en": "Graduation requires a cumulative GPA of at least {value} out of 5 for {degree} students."},
    "RULE-REG-06": {"ar": "يحق لطالب {degree} التظلم من درجة الاختبار النهائي {value} خلال دراسته، ويقدم التظلم خلال ثلاثة أيام من إعلان النتيجة.",
                    "en": "A {degree} student may appeal a final exam grade {value} during their studies; an appeal is submitted within three days of the result."},
}
DEGREE_NAMES = {"ar": {"phd": "الدكتوراه", "master": "الماجستير", "diploma": "الدبلوم العالي"},
                "en": {"phd": "PhD", "master": "master's", "diploma": "higher diploma"}}
APPEAL_WORDS = {"ar": {3: "ثلاث مرات", 2: "مرتين"}, "en": {3: "three times", 2: "twice"}}
REENROL = (["اعاده القيد", "اعاده قيد", "re-enrol", "reenrol", "re-enroll", "reinstat"],
           ["كم فصل", "خلال", "within", "how many", "how long", "كم مره", "times", "once", "again", "مره اخري"],
           {"ar": "يقدم طلب إعادة القيد إلى القسم خلال أربعة فصول دراسية من تاريخ طي القيد، ولا يجوز إعادة القيد أكثر "
                  "من مرة واحدة إلا استثناءً بقرار من مجلس الجامعة.",
            "en": "A re-enrolment request is submitted to the department within four semesters of the closure date, and "
                  "re-enrolment is allowed only once, beyond that only by exception from the university council."})


def statement_sentences(question, language, degree=None, stated_values=()):
    """Return [(rule_id, sentence)] stating rule thresholds the question asks about.

    Used when the student asks what a rule is rather than giving their own number, so
    pass marks, GPA limits, honours, appeals and the re-enrolment window come from the
    rule library and never from the model (end-to-end v1: E059, E061, E062, E064).
    """
    from app.rules.registration_rules import APPEALS, GPA_GRADUATION, GPA_WARNING
    text = normalize_for_search(question)
    out = []
    for rule_id, triggers, sentence in STATEMENTS:
        if any(t in text for t in triggers) and VALUE_INPUT.get(rule_id) not in stated_values:
            out.append((rule_id, sentence[language]))
    limits = {"RULE-REG-03": GPA_WARNING, "RULE-ELIG-01": GPA_GRADUATION, "RULE-REG-06": APPEALS}
    for rule_id, (triggers, sentence) in BY_DEGREE.items():
        if not any(t in text for t in triggers) or VALUE_INPUT.get(rule_id) in stated_values:
            continue
        if rule_id == "RULE-ELIG-01" and not any(w in text for w in ("معدل", "gpa", "average")):
            continue
        if rule_id == "RULE-REG-03" and not any(w in text for w in ("معدل", "gpa", "average", "below", "اقل", "متي", "when")):
            continue
        if rule_id == "RULE-REG-03" and any(w in text for w in ("انذارين", "two consecutive", "two warnings", "two academic")):
            continue
        if rule_id == "RULE-REG-06" and not any(w in text for w in ("كم", "how many", "عدد", "times", "مرات", "مره")):
            continue
        values = limits[rule_id]
        if degree in values:
            value = values[degree]
            shown = APPEAL_WORDS[language][value] if rule_id == "RULE-REG-06" else _number(value)
            out.append((rule_id, DEGREE_ONLY[rule_id][language].format(value=shown, degree=DEGREE_NAMES[language][degree])))
        else:
            out.append((rule_id, sentence[language].format(phd=_number(values["phd"]), diploma=_number(values["diploma"]))))
    words, asks, sentence = REENROL
    if any(w in text for w in words) and any(a in text for a in asks):
        out.append(("RULE-REG-05", sentence[language]))
    return out
