# rules

Generated from `rules/rule_library.json` by `python cli.py rules-doc`; edit the JSON, not this file.

Every rule cites an institutional source, declares its inputs, and has boundary tests in
`tests/test_rules.py`. A missing input returns `unknown`; nothing is filled with a default.
Rules inform the student; they never take an official decision.

## calendar rules

Calendar rules read the academic calendar **in force on `as_of`**. When the question names
no term, `current` rules use the term in progress (first term before it starts) and
`upcoming` rules use the next term to start. The answer states which basis was used.

### RULE-CAL-01: Semester withdrawal window

- **source:** CALENDAR-1448, rows 6 and 18; HANDBOOK-1446, p18 الاعتذار عن الدراسة
- **inputs:** as_of, term_id
- **condition:** as_of <= semester withdrawal deadline of the term
- **outputs:** open, closed
- **effective:** 2024-08-01 to open
- **calendar event:** `SEMESTER_WITHDRAWAL_DEADLINE`, compared `on_or_before`, term basis `current`
- **tests:** test_cal01_boundaries, test_cal_unknown_without_calendar

### RULE-CAL-02: Semester postponement window

- **source:** CALENDAR-1448, rows 4 and 12; HANDBOOK-1446, p17 تأجيل الدراسة
- **inputs:** as_of, term_id
- **condition:** as_of <= postponement deadline of the term
- **outputs:** open, closed
- **effective:** 2024-08-01 to open
- **calendar event:** `POSTPONEMENT_DEADLINE`, compared `on_or_before`, term basis `current`
- **tests:** test_cal02_boundaries

### RULE-CAL-03: Re-enrolment request window

- **source:** CALENDAR-1448, rows 2 and 10; HANDBOOK-1446, p21 إعادة القيد
- **inputs:** as_of, term_id
- **condition:** as_of <= re-enrolment request deadline of the term
- **outputs:** open, closed
- **effective:** 2024-08-01 to open
- **calendar event:** `REENROLLMENT_DEADLINE`, compared `on_or_before`, term basis `upcoming`
- **tests:** test_cal03_boundaries

### RULE-CAL-04: Tuition refund on program withdrawal

- **source:** HANDBOOK-1446, p19 الانسحاب من الجامعة; FAQ-NAUSS, FAQ-NAUSS#020; CALENDAR-1448, rows 3 and 11
- **inputs:** as_of, term_id
- **condition:** as_of < study start date of the term (tuition only; administrative fees are never refunded)
- **outputs:** refund_eligible, refund_not_eligible
- **effective:** 2024-08-01 to open
- **calendar event:** `TERM_START`, compared `before`, term basis `current`
- **tests:** test_cal04_boundaries

### RULE-CAL-05: Program withdrawal request window

- **source:** HANDBOOK-1446, p19 الانسحاب من الجامعة; CALENDAR-1448, rows 7 and 19
- **inputs:** as_of, term_id
- **condition:** as_of < start of final exams of the term
- **outputs:** open, closed
- **effective:** 2024-08-01 to open
- **calendar event:** `FINAL_EXAMS_START`, compared `before`, term basis `current`
- **tests:** test_cal05_boundaries

## regulation rules

### RULE-REG-01: Attendance and exam deprivation

- **source:** HANDBOOK-1446, p23 الحرمان من دخول الاختبار النهائي
- **inputs:** attendance_percent
- **condition:** >= 75% eligible; 50% to under 75% only with an accepted excuse; under 50% deprived
- **outputs:** eligible_for_final, deprived_exception_possible, deprived
- **effective:** 2024-08-01 to open
- **tests:** test_reg01_boundaries

### RULE-REG-02: Course pass mark

- **source:** HANDBOOK-1446, p22 اجتياز المقرر الدراسي
- **inputs:** course_grade
- **condition:** final course grade >= 70 of 100
- **outputs:** passed, failed
- **effective:** 2024-08-01 to open
- **tests:** test_reg02_boundaries

### RULE-REG-03: Academic warning

- **source:** HANDBOOK-1446, p15 الإنذار الأكاديمي
- **inputs:** degree, gpa
- **condition:** GPA < 3.75/5 (PhD, master's) or < 3.00/5 (higher diploma)
- **outputs:** warning, no_warning
- **effective:** 2024-08-01 to open
- **tests:** test_reg03_boundaries

### RULE-REG-04: Enrolment closure after warnings

- **source:** HANDBOOK-1446, p21 طي القيد، البند 5
- **inputs:** consecutive_warnings
- **condition:** two or more consecutive academic warnings
- **outputs:** enrolment_closed, enrolment_continues
- **effective:** 2024-08-01 to open
- **tests:** test_reg04_boundaries

### RULE-REG-05: Re-enrolment eligibility

- **source:** HANDBOOK-1446, p21-22 إعادة القيد
- **inputs:** semesters_since_closure, previous_reenrolments
- **condition:** within 4 semesters of closure and not re-enrolled before
- **outputs:** eligible_to_apply, not_eligible, exception_only
- **effective:** 2024-08-01 to open
- **tests:** test_reg05_boundaries

### RULE-REG-06: Final exam grade appeals remaining

- **source:** HANDBOOK-1446, p26 المادة 34
- **inputs:** degree, appeals_used
- **condition:** 3 appeals (PhD, master's) or 2 (diploma) minus those used
- **outputs:** 0, 1, 2, 3
- **effective:** 2024-08-01 to open
- **tests:** test_reg06_boundaries

### RULE-ELIG-01: Graduation GPA

- **source:** PROGRAMS-GUIDE-1448, متطلبات التخرج; HANDBOOK-1446, p15 الإنذار الأكاديمي
- **inputs:** degree, gpa
- **condition:** GPA >= 3.75/5 (PhD, master's) or >= 3.00/5 (higher diploma)
- **outputs:** meets_gpa, below_gpa
- **effective:** 2024-08-01 to open
- **tests:** test_elig01_boundaries

### RULE-ELIG-02: Graduation honours

- **source:** HANDBOOK-1446, p25 مراتب الشرف
- **inputs:** gpa, failed_any_course, disciplinary_penalty, enrolment_ever_closed
- **condition:** GPA >= 4.75 first, >= 4.50 second; excluded by a failed course, penalty or closure
- **outputs:** first_honours, second_honours, no_honours, not_eligible
- **effective:** 2024-08-01 to open
- **tests:** test_elig02_boundaries

## notes

- **Semester withdrawal:** the handbook says the request is made at least two weeks before
  final exams (latest 2026-11-22 for the first term); the calendar sets 2026-11-19. The calendar
  date is the stricter one and is the date the rule uses.
- **Refunds:** only tuition for a term not yet started is refundable; administrative fees never are.
