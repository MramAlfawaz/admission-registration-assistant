"""Intent labels, their meaning, and the context each one needs."""

INTENTS = {
    "ADMISSION_REQUIREMENTS": "General or program-specific conditions for admission",
    "ADMISSION_DOCUMENTS": "Documents an applicant must provide",
    "ADMISSION_PROCEDURE": "How to apply, application steps, interviews, results, intake rules",
    "FEES": "Application, administrative and tuition fees, payment timing, refunds",
    "PROGRAM_INFORMATION": "Which programs exist, their language, schedule and content",
    "STUDY_DURATION": "Normal and maximum length of study",
    "ACADEMIC_CALENDAR": "Term start, exams, holidays and other calendar dates",
    "POSTPONEMENT": "Postponing (deferring) a semester of study",
    "SEMESTER_WITHDRAWAL": "Withdrawing (apologising) from a whole semester",
    "PROGRAM_WITHDRAWAL": "Withdrawing from the program or the university",
    "COURSE_WITHDRAWAL": "Dropping or adding a single course",
    "WITHDRAWAL_UNSPECIFIED": "Withdrawal without saying course, semester or program",
    "REENROLLMENT": "Re-enrolment after enrolment was closed",
    "ATTENDANCE": "Attendance rules and exam deprivation",
    "GRADING_AND_STANDING": "Grades, GPA, passing marks, academic warnings, appeals",
    "GRADUATION_REQUIREMENTS": "Conditions for graduating, comprehensive exam, thesis",
    "OUT_OF_SCOPE": "Not an admission or registration matter",
}

# Context the answer depends on; a missing item triggers clarification (Stage 3).
# The term is not required: when a question omits it, the calendar rule resolves
# the term in progress on as_of_date and states that basis in the answer.
REQUIRED_CONTEXT = {
    "WITHDRAWAL_UNSPECIFIED": ["withdrawal_scope"],
    "STUDY_DURATION": ["degree_level"],
    "GRADUATION_REQUIREMENTS": ["degree_level"],
}
