# user evaluation and outside test

Two required checks done with people outside the team (brief: Experiment 5 "user evaluation" and
Phase 8; Development Standards: Part 5, definition of done). Neither collects personal data.

## 1. user evaluation (students and staff, reported separately)

**Who:** a small group, for example 3 to 5 students and 1 to 3 staff of the Deanship or any
university staff. Record the limitation if the group is smaller or not from NAUSS.

**How:** give each person the public demo link and these tasks, one at a time. Do not help them;
note where they get stuck.

| # | task (give it in the participant's language) |
|---|---|
| 1 | Find the last day to withdraw from the first semester. |
| 2 | Ask what attendance is required to sit the final exam. |
| 3 | Ask "I want to withdraw" and finish the question the assistant asks back. |
| 4 | Ask for something only staff can decide (for example "approve my admission"). |
| 5 | Ask any question of your own about admission or registration. |

Then ask them to rate **1 to 5** (5 = best):

| column | question |
|---|---|
| `ease` | How easy was it to use? |
| `clarity` | How clear were the answers? |
| `sources` | How useful were the sources shown under each answer? |
| `trust` | How much would you trust these answers? |
| `defensible` | **Staff only:** could you defend these answers to a student if challenged? |

**Record** one row per person in `feedback.csv` (Excel or Numbers, keep it as CSV):
- `participant`: a code such as S1, S2, T1 (never a name)
- `group`: `student` or `staff`
- `date`: YYYY-MM-DD
- `tasks_completed` / `tasks_given`: for example 5 / 5
- the five ratings (leave `defensible` empty for students)
- `comment`: what they said, in a sentence (no personal details)

Then run `python cli.py score-feedback`; results go to `evaluation/results/user_feedback.md`, students
and staff in separate columns with mean, standard deviation and n.

## 2. outside install test (definition of done)

One person who has never seen the code clones the repository, follows the README alone and gets a
correct answer, timed. Fill in this table and commit it.

| date | person (code) | operating system | minutes to first correct answer | passed? | where they got stuck |
|---|---|---|---|---|---|
| | | | | | |

The automated part of this check is `bash scripts/clean_install_check.sh` (fresh clone, install,
bootstrap, tests, reproduce the held-out results); a person following the README is still required.
