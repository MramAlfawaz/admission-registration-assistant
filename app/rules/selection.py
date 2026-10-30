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


def run_rules(engine, intent, question, context, as_of):
    """Run the rules for an intent; rules lacking a stated student value are skipped."""
    inputs = extract_inputs(question, context)
    results = []
    for rule_id in RULES_BY_INTENT.get(intent, []):
        needed = NEEDS_STUDENT_VALUE.get(rule_id)
        if needed and inputs.get(needed) is None:
            continue
        results.append(engine.run(rule_id, as_of, **{k: v for k, v in inputs.items() if v is not None}))
    return results
