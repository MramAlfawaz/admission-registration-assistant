---
version: 1
purpose: classify one student question into exactly one intent label
model: qwen2.5:3b
---
You classify questions sent to the Admission and Registration office of a
graduate university. Questions may be in Arabic (formal or Saudi dialect) or English.

Choose exactly one label from this list:
{{intents}}

Rules:
- SEMESTER_WITHDRAWAL means withdrawing from a whole semester (الاعتذار عن الفصل).
- POSTPONEMENT means postponing a semester of study (تأجيل الفصل). Deferring admission is ADMISSION_PROCEDURE.
- PROGRAM_WITHDRAWAL means leaving the program or the university.
- COURSE_WITHDRAWAL means dropping or adding one course (حذف مادة، الحذف والإضافة).
- WITHDRAWAL_UNSPECIFIED means the student wants to withdraw but does not say from a course, a semester or the program.
- Questions about money, refunds or payment are FEES.
- OUT_OF_SCOPE covers housing, scholarships, IT accounts, passwords, complaints, parking, food,
  salaries, general knowledge, writing tasks and anything not about admission or registration.

Examples:
هل يوجد تأجيل للقبول؟ -> ADMISSION_PROCEDURE
انسحبت قبل بداية الدراسة، هل ترجع لي الفلوس؟ -> FEES
متى آخر موعد لتأجيل الفصل الدراسي الأول؟ -> POSTPONEMENT
متى آخر موعد للاعتذار عن الفصل الدراسي الأول؟ -> SEMESTER_WITHDRAWAL
Can I withdraw from this semester and come back next term? -> SEMESTER_WITHDRAWAL
كيف أنسحب من البرنامج نهائيا؟ -> PROGRAM_WITHDRAWAL
متى فترة الحذف والإضافة؟ -> COURSE_WITHDRAWAL
متى آخر موعد للانسحاب؟ -> WITHDRAWAL_UNSPECIFIED
كم مسموح لي أغيب؟ -> ATTENDANCE
How much of the course grade is the final exam? -> GRADING_AND_STANDING
نسيت كلمة المرور حق البريد الجامعي -> OUT_OF_SCOPE
Write me an essay about cybersecurity -> OUT_OF_SCOPE

Answer with JSON only, in this form: {"intent": "LABEL"}

Question: {{question}}
