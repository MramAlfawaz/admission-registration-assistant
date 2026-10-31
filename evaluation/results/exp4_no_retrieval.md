# Experiment 4: no retrieval (A) against the grounded assistant (B)

Set `inquiries` (100 inquiries). A: `prompts/no_retrieval_v1.md`, same model, no evidence, no rules, no checks; never shown to a student.

B: `e2e_v2.json`.

| metric | A: no retrieval | B: grounded assistant |
|---|---|---|
| fully correct (all inquiries) | 0.14 | 0.82 |
| answerable inquiries answered correctly | 0.086 | 0.757 |
| non-answer inquiries refused or escalated | 0.267 | 1.0 |
| wrong answers shown | 79 | 13 |
| grounded claim rate (judged) | 0.153 | 0.772 |
| unsupported claim rate (judged) | 0.847 | 0.228 |
| English claims not judged | 47 | 30 |

**ar:** A correct 0.133, wrong shown 47; B correct 0.85, wrong shown 7

**en:** A correct 0.15, wrong shown 32; B correct 0.775, wrong shown 6

## sample of condition A answers

- **E001** (ANSWERABLE) متى تبدأ الاختبارات النهائية للفصل الأول؟ → لا يمكنني تحديد تاريخ محدد لبدء الاختبارات النهائية للفصل الأول من العام الدراسي 2026-10-14، حيث أن هذا يتطلب معرفة مواعيد الاختبارات النهائية المعلنة رسمياً من قبل NAUSS.
- **E002** (ANSWERABLE) متى تبدأ إجازة عيد الفطر هذا العام الدراسي؟ → عذرًا، لا يمكنني تحديد التاريخ الدقيق لإجازة عيد الفطر لهذا العام الدراسي 2026-10-14، حيث أنه لم يتم الإعلان عنه رسمياً حتى الآن.
- **E003** (ANSWERABLE) متى تبدأ إجازة نهاية العام الدراسي؟ → لا يمكن تحديد تاريخ بدء إجازة نهاية العام الدراسي في 2027، حيث أن هذا التاريخ غير موجود. يرجى الرجوع إلى الموقع الرسمي للجامعة أو التواصل مع مكتب القبول للحصول على المعلومات الأكثر دقة.
- **E004** (ANSWERABLE) هل أقدر أأجل الترم الثاني الحين؟ → عذراً، لا يمكن تأجيل ترم الثانوي في الوقت الحالي.
- **E005** (ANSWERABLE) هل ما زال بإمكاني تأجيل الفصل الدراسي الأول؟ → نعم، ما زال بإمكانك تأجيل الفصل الدراسي الأول، ولكن يجب عليك الاتصال بالجامعة للحصول على التفاصيل المحددة.
- **E006** (ANSWERABLE) إلى متى أقدر أعتذر عن الترم الثاني؟ → أعتذر عن الترم الثاني حتى 31/08/2027
- **E007** (ANSWERABLE) انطوى قيدي، إلى متى أقدر أقدم على إعادة القيد للترم الثاني؟ → أقدر أقدم على إعادة القيد للترم الثاني حتى نهاية فترة الدراسة في الترم الأول من العام الدراسي نفسه.
- **E008** (ANSWERABLE) متى يبدأ الفصل الدراسي الأول؟ → في 2026-08-01 لا يوجد فصل دراسي في NAUSS في هذا التاريخ.
- **E009** (ANSWERABLE) On which day of the week do first-semester final exams begin? → The specific day of the week for the first-semester final exams beginning at Naif Arab University for Security Sciences (NAUSS) in Riyadh, Saudi Arabia in 2026 is not provided in the given information
- **E010** (ANSWERABLE) When does the mid-year break begin? → The mid-year break schedule for Naif Arab University for Security Sciences (NAUSS) in Riyadh, Saudi Arabia, varies each academic year and is typically announced by the university closer to the start o
- **E011** (ANSWERABLE) What was the last day to postpone the second semester? → The last day to postpone the second semester for NAUSS in Riyadh, Saudi Arabia is not provided in the current information and would need to be checked on the official NAUSS website or contacting their
- **E012** (ANSWERABLE) Is the first-semester withdrawal period still open? → The withdrawal period for the first semester typically opens in early October and closes in mid-October. Please check the NAUSS website for the most accurate and up-to-date information for the year 20
- **E013** (ANSWERABLE) Is it too late to ask for re-enrolment in the first semester? → It is generally not advisable to ask for re-enrollment in the first semester as the university typically has a set application period for each semester. You should check the NAUSS admission and regist
- **E014** (ANSWERABLE) When does study resume after the Eid al-Adha holiday? → The exact date for the resumption of study after Eid al-Adha varies each year, but typically it is around the second week of April. Please check the NAUSS website or contact their admissions office fo
- **E015** (ANSWERABLE) ما التقدير المطلوب في البكالوريوس للتقديم على الدبلوم العالي؟ → لا يوجد تقدير مطلوب للبكالوريوس للتقديم على الدبلوم العالي في NAUSS، حيث يتم النظر في عدة عوامل أخرى مثل المؤهلات السابقة والخبرة العملية.
