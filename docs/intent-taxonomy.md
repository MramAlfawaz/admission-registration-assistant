# intent taxonomy

17 labels, built from what the six source documents actually cover and from how
students phrase questions. Defined in `app/intent/taxonomy.py`; this file is the
human reference used when labelling `evaluation/intent/questions.jsonl`.

| intent | meaning | example (ar) | example (en) | supported by |
|---|---|---|---|---|
| ADMISSION_REQUIREMENTS | general or program-specific admission conditions | هل لازم ايلتس للماجستير؟ | Do I need an English test? | ADMISSION-PAGE, PROGRAMS-GUIDE, FAQ |
| ADMISSION_DOCUMENTS | documents an applicant provides | وش الأوراق المطلوبة؟ | What documents do I submit? | ADMISSION-PAGE |
| ADMISSION_PROCEDURE | how to apply, steps, interview, results, intake rules | كيف أقدم؟ | How do I apply? | ADMISSION-PAGE, FAQ |
| FEES | application, administrative, tuition fees, payment, refunds | كم رسوم الماجستير؟ | Is the application fee refundable? | PROGRAMS-GUIDE, ADMISSION-PAGE, FAQ, HANDBOOK |
| PROGRAM_INFORMATION | programs offered, language, schedule | هل الدراسة مسائية؟ | Is the program taught in English? | PROGRAMS-GUIDE, FAQ |
| STUDY_DURATION | normal and maximum length of study | كم مدة الماجستير؟ | How long is the diploma? | PROGRAMS-GUIDE, FAQ, HANDBOOK |
| ACADEMIC_CALENDAR | term start, exams, holidays | متى تبدأ الدراسة؟ | When are final exams? | CALENDAR |
| POSTPONEMENT | postponing a semester | أبي أأجل الترم | Can I postpone a semester? | HANDBOOK, CALENDAR |
| SEMESTER_WITHDRAWAL | withdrawing from a whole semester (اعتذار) | متى آخر موعد للاعتذار؟ | Semester withdrawal deadline? | HANDBOOK, CALENDAR |
| PROGRAM_WITHDRAWAL | leaving the program or university | كيف أنسحب من البرنامج؟ | How do I withdraw from the program? | HANDBOOK, FAQ |
| COURSE_WITHDRAWAL | dropping or adding one course | اقدر اسحب المادة؟ | Can I drop a course? | **none**: answered as INSUFFICIENT_EVIDENCE |
| WITHDRAWAL_UNSPECIFIED | withdrawal without saying what from | هل أقدر أنسحب؟ | Can I withdraw? | triggers clarification |
| REENROLLMENT | re-enrolment after enrolment was closed | كيف أعيد القيد؟ | Can I re-enroll? | HANDBOOK, CALENDAR |
| ATTENDANCE | attendance rule and exam deprivation | كم نسبة الحضور؟ | Minimum attendance? | HANDBOOK |
| GRADING_AND_STANDING | grades, GPA, passing mark, warnings, appeals | كم درجة النجاح؟ | What is the passing mark? | HANDBOOK |
| GRADUATION_REQUIREMENTS | graduating, comprehensive exam, thesis, honours | متطلبات التخرج؟ | What do I need to graduate? | HANDBOOK, PROGRAMS-GUIDE |
| OUT_OF_SCOPE | anything else | وين المواقف؟ | Is there student housing? | routed, never answered |

## required context
A missing value triggers one clarification question (Stage 3). Values are only
taken from the question; nothing is filled with a default.

| intent | required | why |
|---|---|---|
| WITHDRAWAL_UNSPECIFIED | withdrawal_scope (course / semester / program) | rules, deadlines and consequences differ |
| STUDY_DURATION | degree_level (phd / master / diploma) | durations differ by level |
| GRADUATION_REQUIREMENTS | degree_level | GPA threshold and exams differ by level |

The term is **not** required: when a deadline question omits it, the calendar
rule resolves the term in progress on `as_of_date` and states that basis.

## decisions
- **Housing** appears in the FAQ, but the brief lists housing as out of scope, so it is routed as OUT_OF_SCOPE.
- **Scholarships** are OUT_OF_SCOPE because the scholarship document is not in the knowledge base.
- **COURSE_WITHDRAWAL** is kept as a label even though no source covers it, so the
  system recognises the question and answers INSUFFICIENT_EVIDENCE instead of
  confusing it with semester withdrawal.
- **Requests for decisions** (approve my admission, grant an exception) keep their
  topic intent; the safety layer assigns STAFF_REVIEW_REQUIRED.

## question set
`evaluation/intent/questions.jsonl`: 155 synthetic questions (87 Arabic, 64 English,
4 mixed), formal and informal, 15 ambiguous. Every third question is the `dev`
split (51) used while building; the remaining 104 are `test`, never used for tuning.
