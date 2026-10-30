"""Threshold rules from the academic regulations (HANDBOOK-1446).

Each function returns (output, details). Thresholds are written once here and
cited in rules/rule_library.json; they inform the student and never decide a case.
"""

GPA_WARNING = {"phd": 3.75, "master": 3.75, "diploma": 3.00}
GPA_GRADUATION = {"phd": 3.75, "master": 3.75, "diploma": 3.00}
APPEALS = {"phd": 3, "master": 3, "diploma": 2}


def attendance(attendance_percent):
    """75% or more may sit the final; 50% to under 75% only by exception; under 50% deprived."""
    p = float(attendance_percent)
    if p >= 75:
        return "eligible_for_final", {"threshold": 75}
    if p >= 50:
        return "deprived_exception_possible", {"threshold": 75, "exception_minimum": 50,
                                               "exception_requires": "accepted excuse and council approval"}
    return "deprived", {"threshold": 75, "exception_minimum": 50}


def course_pass(course_grade):
    """A course is passed with a final grade of 70 out of 100 or more."""
    return ("passed" if float(course_grade) >= 70 else "failed"), {"pass_mark": 70}


def academic_warning(degree, gpa):
    """A warning is issued below 3.75/5 (PhD, master's) or 3.00/5 (higher diploma)."""
    if degree not in GPA_WARNING:
        return "unknown", {"reason": f"unknown degree: {degree}"}
    limit = GPA_WARNING[degree]
    return ("warning" if float(gpa) < limit else "no_warning"), {"threshold": limit, "scale": 5}


def enrolment_closure(consecutive_warnings):
    """Enrolment is closed after two consecutive academic warnings."""
    n = int(consecutive_warnings)
    return ("enrolment_closed" if n >= 2 else "enrolment_continues"), {"limit": 2}


def reenrolment_eligibility(semesters_since_closure, previous_reenrolments):
    """Re-enrolment within four semesters of closure, once; later only by council exception."""
    if int(previous_reenrolments) >= 1:
        return "exception_only", {"reason": "re-enrolment is allowed once; more needs a university council decision"}
    if int(semesters_since_closure) > 4:
        return "not_eligible", {"limit_semesters": 4}
    return "eligible_to_apply", {"limit_semesters": 4, "approval": "department, college and deanship councils"}


def appeals_remaining(degree, appeals_used):
    """Three final-exam grade appeals for PhD and master's students, two for diploma students."""
    if degree not in APPEALS:
        return "unknown", {"reason": f"unknown degree: {degree}"}
    left = max(0, APPEALS[degree] - int(appeals_used))
    return str(left), {"limit": APPEALS[degree]}


def graduation_gpa(degree, gpa):
    """Graduation needs a cumulative GPA of at least 3.75/5 (PhD, master's) or 3.00/5 (diploma)."""
    if degree not in GPA_GRADUATION:
        return "unknown", {"reason": f"unknown degree: {degree}"}
    limit = GPA_GRADUATION[degree]
    return ("meets_gpa" if float(gpa) >= limit else "below_gpa"), {"threshold": limit, "scale": 5}


def honours(gpa, failed_any_course, disciplinary_penalty, enrolment_ever_closed):
    """First honours from 4.75, second from 4.50; never with a failed course, penalty or closure."""
    g = float(gpa)
    level = "first_honours" if g >= 4.75 else "second_honours" if g >= 4.50 else "no_honours"
    if level != "no_honours" and (failed_any_course or disciplinary_penalty or enrolment_ever_closed):
        return "not_eligible", {"reason": "a failed course, a disciplinary penalty or a closed enrolment excludes honours"}
    return level, {"first": 4.75, "second": 4.50,
                   "also_required": "graduation within the average of the minimum and maximum duration"}
