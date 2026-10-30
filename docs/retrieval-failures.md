# retrieval failure analysis

Experiment 2, hybrid retrieval (the default method), gold set v1 of 64 questions,
run on 2026-10-30. A failure is a question whose supporting passage was not in
the top 10 (`recall@10 < 1`). Results file: `evaluation/results/retrieval_hybrid.json`.

## summary

| | questions | failures at top 10 |
|---|---|---|
| Arabic | 39 | **0** |
| English (cross-language: every source is Arabic) | 25 | **8** |
| total | 64 | 8 |

Every failure is an English question. Each was reviewed by hand against the
passages actually retrieved; the automatic label "cross-language vocabulary
mismatch" was replaced by the specific cause below.

| cause | count | questions |
|---|---|---|
| English grading table attracts English questions | 2 | R008, R021 |
| gold annotation too strict (valid evidence was retrieved) | 2 | R017, R041 |
| program details split from the program title by page layout | 1 | R054 |
| similar program names (master's vs higher diploma) | 1 | R056 |
| cross-language meaning drift toward a dominant topic | 2 | R019, R050 |

## each failure

### R008: "If I withdraw from a semester, do I get my fees back?"
- expected: `HANDBOOK-1446#011` (an apologising student may not recover paid fees)
- retrieved first: `HANDBOOK-1446#018`, the grading table, which is the only English text in the handbook and contains the word "Withdraw"
- also retrieved: `FAQ-NAUSS#020`, which is about refunds after **program** withdrawal, a different rule
- cause: **English grading table attracts English questions**
- risk: an answer built from FAQ-NAUSS#020 would apply the wrong refund rule. Evidence validation (phase 6) must check that the retrieved rule matches the intent (semester vs program).

### R017: "What is the passing mark for a course?"
- expected: `HANDBOOK-1446#015` ("passing grade is 70")
- retrieved: `HANDBOOK-1446#018` and `#017`, the grade scale, where marks below 70 are "Fail"
- cause: **gold annotation too strict**. #017 answers the question indirectly through the scale; #015 states it directly. The gold set is left unchanged so the reported number stays comparable.

### R019: "What happens after two consecutive academic warnings?"
- expected: `HANDBOOK-1446#014` (enrolment is closed after two consecutive warnings)
- retrieved: graduation-GPA passages from the programs guide
- cause: **meaning drift**. "Academic warning" sits close to "GPA" in the embedding space, and the answer is item 5 of a 10-item list inside #014, so the passage as a whole is about many other reasons for closing enrolment.

### R021: "How do I appeal a final exam grade?"
- expected: `HANDBOOK-1446#019` or `#020` (grade appeal procedure)
- retrieved first: `HANDBOOK-1446#017`, the English grade table ("Grade", "Mark")
- cause: **English grading table attracts English questions**

### R041: "Is the administrative fee refundable?"
- expected: `ADMISSION-PAGE-2025#001` or `PROGRAMS-GUIDE-1448#005` (administrative fee is non-refundable)
- retrieved first: `FAQ-NAUSS#020`, which says tuition is refundable "without the administrative fees"
- cause: **gold annotation too strict**. FAQ-NAUSS#020 does answer the question. It was missed when the gold set was written.

### R050: "Are there evening programs?"
- expected: `FAQ-NAUSS#013` (some programs are morning, some evening)
- retrieved: program descriptions from the programs guide
- cause: **meaning drift toward a dominant topic**. The guide has dozens of passages about "programs", which outweigh the one short FAQ answer.

### R054: "Is the secure AI master's program taught in English?"
- expected: `PROGRAMS-GUIDE-1448#020`
- retrieved: `#019` (the same program's admission rules, which mention English proficiency), `#021`, `#018`
- cause: **page layout**. Each program's language, duration and fee box is printed in a side panel that extraction places after the program's last section, so it lands in the same passage as the start of the **next** program. The right program was found, but not the passage holding its language box.

### R056: "Does the national security master's require work experience?"
- expected: `PROGRAMS-GUIDE-1448#028` (three years' experience required)
- retrieved first: `#036`, the admission rules of the **higher diploma** in national security
- cause: **similar program names**. The master's and the higher diploma share the name "national security".

## what this changes

1. **Arabic retrieval is reliable** (recall@10 = 1.0). English questions are the weak point (recall@10 = 0.68).
2. **Phase 6 must check rule applicability**, not only presence: R008 shows a related but wrong rule (program withdrawal) can rank above the right one.
3. **Candidate improvements**, chosen after seeing these results and therefore to be tested on new English questions not in this gold set:
   - translate English questions into Arabic with the local model before searching
   - skip BM25 for English questions, since no source is in English
   - chunk the programs guide at program boundaries so each program's details stay together
4. **Gold set**: R017 and R041 show two annotations were too strict. The set is kept unchanged (v1) so results stay comparable; any correction will be released as v2 with both scores reported.
