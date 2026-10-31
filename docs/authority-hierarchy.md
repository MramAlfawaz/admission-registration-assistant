# authority hierarchy

Required by the brief (Section 12). It records which document type wins when two approved
documents disagree. **Status: assumed by the developer; not yet agreed with the Deanship of
Admission and Registration.** The brief asks for this to be agreed with the department; until it
is, every resolved conflict is also flagged for department review (`conflict-report`).

## order of authority (1 = highest)
| level | document type | source in this project | reason |
|---|---|---|---|
| 1 | regulation | HANDBOOK-1446 (student handbook: summary of the academic regulations) | the regulations are the legal basis; every other document applies them |
| 2 | academic calendar | CALENDAR-1448 | the official dates for the year; issued under the regulations |
| 3 | program requirements | PROGRAMS-GUIDE-1448 (PROGRAMS-GUIDE-1447 superseded) | program-specific conditions, fees and durations for the admission year |
| 4 | procedure page | ADMISSION-PAGE-2025 | how to apply; a web page, may be updated without notice |
| 5 | FAQ | FAQ-NAUSS | short answers written for convenience; undated |

## resolution order (`app/evidence/contradiction.py`)
When two passages state different values for the same fact (same type, kind and subject):
1. **status**: an approved document beats a superseded one
2. **authority level**: the lower number wins (table above)
3. **effective date**: the more recent effective date wins
4. otherwise the conflict is **unresolved**: the answer is blocked with `CONFLICTING_EVIDENCE`
   and the student is referred to the Deanship

The losing passage is removed from the evidence for that answer and listed for review.

## special cases
- **Calendar against regulation on a date.** The handbook says a semester withdrawal request is made
  at least two weeks before final exams (latest 2026-11-22 for term 1); the calendar sets 2026-11-19.
  The calendar date is the stricter one and is the date the rule uses (`docs/rules.md`).
- **A document is never in conflict with itself**; differences inside one document are left to the reader.
- **Dates not stated in a document** are set by the developer and marked `dates_assumed: true` in
  `data/sources.json`. An assumed date can decide which version is in force; this is a limitation.

## known false conflict
The phase 6 "criminology duration" conflict (FAQ two years against the 1448 guide one year) is an
extraction error: in the 1448 guide each program's box is extracted before its title. It is not a
disagreement between documents (`docs/evidence-validation.md`).
