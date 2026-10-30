"""Fixed sentences for rule results: dates, open/closed and thresholds are never left to the model."""
import datetime as dt

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
