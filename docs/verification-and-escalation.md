# clarification, verification and escalation

Phases 9 and 10. They exist because of real failures seen on 2026-10-31 with
`answer_v1` (see the regression tests in `tests/test_generation.py`):

| failure seen | example | fix |
|---|---|---|
| closed window not stated, student told to submit | "When is the semester withdrawal deadline?" on 2026-12-01 | rule results become fixed sentences written by code |
| wrong weekday | "Friday 2026-11-19" (calendar: Thursday) | weekday computed by code; verifier rejects weekdays not in evidence |
| no clarification for an ambiguous question | "هل أقدر أنسحب؟" classified as semester withdrawal | ambiguity read from the question text, not from the intent |
| false "no information" and Chinese characters | law-enforcement experience question | verifier rejects both; answer falls back to quoted evidence |
| program-withdrawal rule mixed into a semester answer | semester withdrawal conditions | relevance filter (phase 6) and prompt v2 |

## clarification (`app/intent/ambiguity.py`)
- **withdrawal scope** is asked when the question uses a generic withdrawal word
  (انسحب, withdraw) and names no course, semester or program. `اعتذار` counts as semester.
- **degree level** is asked only for duration or graduation questions that name no degree and no program.
- One question is asked, with options. The reply is passed back
  (`python cli.py ask "..." --as-of ... --clarify withdrawal_scope=semester`), sets the intent,
  and is added to the search query.

## answer composition (`app/pipeline/assistant.py`)
1. Rule results are turned into fixed sentences (`app/generation/rule_sentences.py`),
   with the weekday computed from the date and "open" or "closed" stated explicitly.
2. The model (`prompts/answer_v2.md`) adds 1 to 3 sentences of explanation from the evidence.
3. The verifier checks the model text. If it fails, or the model output is unusable, the
   explanation is replaced by the 1 or 2 evidence sentences closest to the question,
   quoted (`app/generation/extractive.py`).
4. Sources are attached by code. `verified` is set only by the pipeline.

## verifier checks (`app/safety/verifier.py`)
| check | rejects |
|---|---|
| script | any character outside Arabic, Latin, digits and punctuation |
| language | an Arabic answer that is under 60% Arabic letters, or an English answer over 20% |
| numbers | any number or date part not present in the evidence, rule results or question |
| weekdays | a weekday not present in the evidence |
| identifiers | internal ids such as `CALENDAR-1448` or `[E1]` |
| no-information claims | "no information" when evidence was found |
| authority boundary | wording that states or implies acceptance, approval or exemption |
| closed windows | advice to submit when a rule says the period has closed |

Spelled-out numbers (ثلاث سنوات) are not checked; this is a known limitation.

## escalation (`app/safety/escalation.py`)
`STAFF_REVIEW_REQUIRED` is returned for:
- requests for a decision or an exception (استثناء, approve, will I be accepted)
- rule results that only a council can grant (`deprived_exception_possible`, `exception_only`)
- questions that need the student's own record (كم معدلي, my grades)

The response states the reason, what can be confirmed (with sources), and the next step.
Each escalation is appended to `data/processed/escalations.jsonl` with reason, intent and
sources, never the question text (`docs/data-handling.md`).
