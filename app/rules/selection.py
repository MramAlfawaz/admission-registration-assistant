"""Choose which rules apply to an intent and read their inputs from the question."""
import re

from app.documents.normalize import normalize_for_search

RULES_BY_INTENT = {
    "SEMESTER_WITHDRAWAL": ["RULE-CAL-01"],
    "POSTPONEMENT": ["RULE-CAL-02"],
    "REENROLLMENT": ["RULE-CAL-03"],
    "PROGRAM_WITHDRAWAL": ["RULE-CAL-05", "RULE-CAL-04"],
    "ATTENDANCE": ["RULE-REG-01"],
    "GRADING_AND_STANDING": ["RULE-REG-02", "RULE-REG-03"],
    "GRADUATION_REQUIREMENTS": ["RULE-ELIG-01"],
}
# Rules that need a number the student must state; skipped when it is absent.
NEEDS_STUDENT_VALUE = {"RULE-REG-01": "attendance_percent", "RULE-REG-02": "course_grade",
                       "RULE-REG-03": "gpa", "RULE-ELIG-01": "gpa"}


def extract_inputs(question, context):
    """Read rule inputs the student wrote: attendance %, GPA, course grade, degree, term.

    Only explicit numbers are read; nothing is assumed.
    """
    text = normalize_for_search(question).translate(str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789"))
    values = dict(context.get("values", {}))
    inputs = {"degree": values.get("degree"), "term_id": values.get("term")}
    pct = re.search(r"(\d{1,3}(?:\.\d+)?)\s*%", text)
    if pct and any(w in text for w in ("حضور", "حضوري", "attendance", "غياب")):
        inputs["attendance_percent"] = float(pct.group(1))
    gpa = re.search(r"(\d\.\d{1,2})", text)
    if gpa and any(w in text for w in ("معدل", "gpa")):
        inputs["gpa"] = float(gpa.group(1))
    grade = re.search(r"(?:درجتي|درجه|grade|mark)\D{0,12}(\d{1,3})", text)
    if grade and not inputs.get("gpa"):
        inputs["course_grade"] = float(grade.group(1))
    return inputs


# Words that ask about timing or whether a window is still open (search form). A deadline
# sentence answers only these; "how many semesters can I postpone?" is not about a date
# (end-to-end v1: E045, E050, E053 got deadline sentences nobody asked for).
TIMING = ["متي", "موعد", "اخر يوم", "لين متي", "الي متي", "فات", "فاتني", "الحين", "الان", "ما زال", "مازال",
          "لا يزال", "still", "deadline", "when", "too late", "last day", "open", "by when", "until when", "date"]
# A yes/no "can I ...?" asks whether the window is open now; "how many semesters can I ...?" does not.
CAN_I = [" هل اقدر", " هل يمكنني", " هل استطيع", " هل ممكن", " هل يحق لي", " can i ", " may i ", " is it possible"]
REFUND = ["استرد", "يسترد", "استرداد", "ترد", "تسترد", "refund", "back", "money"]
DEADLINE_RULES = {"RULE-CAL-01", "RULE-CAL-02", "RULE-CAL-03", "RULE-CAL-05"}
# Rules triggered by what the question says, whatever intent the classifier chose
# (end-to-end v1: refund question classified as fees, GPA warning classified as graduation).
TRIGGERS = [
    ("RULE-CAL-01", [["اعتذار", "اعتذر", "معتذر"]]),
    ("RULE-CAL-01", [["withdraw"], ["semester", "term"]]),
    ("RULE-CAL-02", [["تاجيل", "اجل ", "اأجل", "postpone", "defer"]]),
    ("RULE-CAL-03", [["اعاده القيد", "اعاده قيد", "re-enrol", "reenrol", "re-enroll", "reinstat"]]),
    ("RULE-CAL-05", [["انسحب", "انسحاب", "withdraw"], ["البرنامج", "الجامعه", "program", "university"]]),
    ("RULE-CAL-04", [["انسحب", "انسحاب", "withdraw"], ["البرنامج", "الجامعه", "program", "university"]]),
    ("RULE-REG-03", [["انذار", "warning"]]),
    ("RULE-ELIG-01", [["تخرج", "اتخرج", "graduat"]]),
]


def asks_timing(question):
    """True when the question asks when, or whether a period is still open."""
    text = f" {normalize_for_search(question)} "
    return any(w in text for w in TIMING) or any(text.startswith(w) or f"، {w.strip()}" in text for w in CAN_I)


def rules_for(intent, question):
    """Rules for the intent plus rules the question's own words call for, deadline rules only on timing."""
    text = f" {normalize_for_search(question)} "
    triggered = {r for r, groups in TRIGGERS if all(any(w in text for w in g) for g in groups)}
    # Threshold rules about a GPA answer only questions that name what the GPA is for.
    chosen = [r for r in RULES_BY_INTENT.get(intent, []) if r not in ("RULE-REG-03", "RULE-ELIG-01") or r in triggered]
    for rule_id, groups in TRIGGERS:
        if rule_id not in chosen and all(any(w in text for w in g) for g in groups):
            chosen.append(rule_id)
    timing, refund = asks_timing(question), any(w in text for w in REFUND)
    return [r for r in chosen if (r not in DEADLINE_RULES or timing) and (r != "RULE-CAL-04" or timing or refund)]


def run_rules(engine, intent, question, context, as_of):
    """Run the rules the question needs; rules lacking a stated student value are skipped."""
    inputs = extract_inputs(question, context)
    results = []
    for rule_id in rules_for(intent, question):
        needed = NEEDS_STUDENT_VALUE.get(rule_id)
        if needed and inputs.get(needed) is None:
            continue
        results.append(engine.run(rule_id, as_of, **{k: v for k, v in inputs.items() if v is not None}))
    return results
