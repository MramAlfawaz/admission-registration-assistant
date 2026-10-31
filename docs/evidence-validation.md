# evidence validation

Stage 5 of the brief. Runs on retrieved passages **before** any answer is generated,
always in this order (`app/evidence/validator.py`):

| step | module | question it answers | failure outcome |
|---|---|---|---|
| 0. currency | `currency_checker.py` | is every passage from a version in force on `as_of`? | passage rejected |
| 1. relevance | `relevance.py` | is the passage about the situation asked (semester vs program withdrawal)? | passage set aside as off topic |
| 2. contradiction | `facts.py`, `contradiction.py` | do sources state different values for the same thing? | resolved, or `CONFLICTING_EVIDENCE` |
| 3. completeness | `completeness.py` | which conditions must the answer keep, and is a needed source missing? | `INSUFFICIENT_EVIDENCE` |

Retrieval already filters by date; currency is checked again so a defect upstream can
never put a superseded rule in an answer.

## facts compared
| type | examples | normalised value |
|---|---|---|
| duration | عامان دراسيان, أربعة فصول, عام دراسي | number of semesters (4, 4, 2) |
| money | 100 ريال, 2000 ريال | integer SAR, with kind: application, administrative, tuition, extra semester, supplementary |
| percent | 75% حضور | integer, kind attendance or other |
| gpa | 3.75 من 5, 5 من3.75 | float, kind graduation, warning, supplementary |
| date | 2026-11-19, 19 نوفمبر 2026 | month-day plus year, kind = calendar event |

Each fact carries a **subject** (degree, program, term) read from the 100 characters
before it; the closest mention wins. Two facts conflict only when type, kind and
subject agree, they come from different sources, and their values differ. A document
is never in conflict with itself.

Only fact types that answer the intent are compared (durations for STUDY_DURATION,
dates for deadline intents, and so on), which keeps unrelated numbers out.

## resolution
Status, then authority level, then effective date, as documented in
`docs/authority-hierarchy.md`. A tie on all three returns `CONFLICTING_EVIDENCE` and
the answer is blocked. The losing passage is removed from the evidence and flagged for
department review.

## results
- Planted set (`evaluation/conflicts/planted.jsonl`, 20 cases: 11 conflicts, 6 near
  misses, 3 currency/relevance/completeness cases): detection rate 1.0, false-positive
  rate 0.0, resolution accuracy 1.0.
- Real documents: the FAQ says every master's takes 2 years; the 1448 guide appeared to say
  the MA in Criminology takes 1 year. Detected and resolved for the guide by authority
  (`tests/test_evidence.py::test_known_real_conflict_criminology_duration`).
  **Correction (2026-10-31):** this is not a real conflict. In the 1448 guide each program's
  duration box is extracted before the program's title; the one-year box belongs to the
  human-rights diploma that follows. The 1447 guide, where the box follows the title, gives
  the criminology master's 2 years. The test still shows that detection and resolution work,
  but the resolved answer (1 year) would be wrong. Fix: chunk the guide at program boundaries.
- `python cli.py conflict-report` writes `evaluation/results/conflict_report.md`, the list
  of conflicts met while answering the gold questions, for the department.

## limitations
- The planted set was written by the developer alongside the code, so its perfect score
  is optimistic; the real-document check is the stronger evidence.
- In the programs guide, a program's duration and fee box often names no program
  (page layout), so its subject is empty and treated as general.
- Condition extraction is a keyword heuristic; verification (phase 10) checks the answer
  keeps the conditions.
