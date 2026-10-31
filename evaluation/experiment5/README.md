# Experiment 5: team review, claim review and efficiency

Specialists from the Deanship were not available, so this is a **documented team review**, the
substitute the brief allows (Experiment 5), and the limitation is stated in the results.

## 1. rate the answers (`rating_sheet.csv`)
Open in Excel or Numbers. For each row give **1 to 5** in each criterion, your name or initials in
`rater`, and a note when a score is 2 or lower. Judge against the approved documents, not memory.

| score | correctness | completeness | relevance | clarity | source appropriateness |
|---|---|---|---|---|---|
| 5 | every fact right | everything a student needs (dates, conditions, next step) | answers exactly what was asked | clear on first reading | cites the passage that states it |
| 4 | right, one minor slip | one small thing missing | mostly on the question | clear, slightly long | right document, broad section |
| 3 | partly right | important detail missing | partly off the question | needs rereading | related but not the exact passage |
| 2 | mostly wrong | most of it missing | mostly off the question | confusing | weakly related |
| 1 | wrong or harmful | nothing useful | unrelated | unreadable | wrong or no source |

For refusals, clarifications and escalations, rate whether that response was the **right thing to
do** (correctness), whether it says why and what to do next (completeness), and its clarity.

## 2. label the claims (`claim_review.csv`)
For each claim, read the evidence and write `grounded` (the evidence states it) or `unsupported` in
`human_label`. The English claims could not be judged automatically; the Arabic rows check how often
the automatic label agrees with a person.

## 3. score
```bash
python cli.py score-ratings
python cli.py score-claims
python cli.py efficiency-report
```
Results go to `evaluation/results/exp5_*.md`.

## 4. optional: user feedback
If you can, ask two or three students and one staff member to try the page and rate 1 to 5: ease of
use, clarity, usefulness of sources, trust. Record them separately (students and staff) in
`user_feedback.csv` with columns `group, ease, clarity, sources, trust, comment`.
