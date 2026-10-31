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
**What can be confirmed is only code-written text**: the fixed rule sentences and verbatim quotes from
the documents (relevant to the question, not contradicting a rule, about the term asked). Model
sentences are never shown there, because a model sentence can imply the student meets the
conditions while the decision belongs to staff (found by hand testing in step 12; fixed in step 13).
The sources listed are those of the rules and the quotes.
Each escalation is appended to `data/processed/escalations.jsonl` with reason, intent and
sources, never the question text (`docs/data-handling.md`).

## phase 10b: per-sentence filter (`app/safety/sentence_filter.py`)

Replaying the real outputs of phase 10 (`evaluation/results/generation_sample_after.json`,
`smoke_after.json`) showed that checking the whole model text at once is not enough:
the text passed the verifier yet still contained wrong content.

| failure seen | example | check |
|---|---|---|
| another situation mixed in | semester withdrawal answer says "you can withdraw from the program and study the supplementary term" | `OTHER_SITUATION` words per intent |
| glossary terms copied | "according to the honours rank" in a re-enrolment answer | a glossary term must appear in the evidence |
| prompt placeholders echoed | condition "conditions written in the evidence" | `PROMPT_ECHO` phrases |
| internal term id leaked | "1448-T1" | `\d{4}-T[12]` |
| speculation | "قد لا يكون لديهم خيارات" | `SPECULATION` words |
| fixed sentence repeated | the deadline sentence written twice | 60% token overlap with a rule sentence |
| invented wording | Arabic sentence mostly made of words not in the evidence | under 50% token overlap |

Each sentence is judged alone: good sentences are kept, bad ones are dropped and recorded
in `_trace.verification_issues`. Harmless openings ("بناءً على المعلومات المقدمة،") are trimmed,
not rejected. Conditions must be real sentences (4 words or more) that pass the same checks.
If no model sentence survives, the answer is the fixed rule sentences plus 1 or 2 quoted
evidence sentences (6 or more words each); with neither, the status is `INSUFFICIENT_EVIDENCE`.

The glossary is now sent to the model only for English answers, and only the terms whose
Arabic form is in the evidence, because the small model copied every glossary term it saw.

Known cost: a correct sentence can be dropped when it also quotes the prompt
(R043: "النص الأول من الأدلة"). Dropping is the safe side: the answer falls back to quotes.

## sentences that imply a decision (step 13)
Besides explicit decisions ("you are accepted", "تم قبولك"), a sentence saying the student **meets the
conditions** ("استوفيت جميع الشروط", "you are eligible", "you have met") is dropped unless it is
conditional ("إذا كنت تستوفي...", "if you meet..."). The system states conditions; it never says whether
a particular student meets them.

## quotes about the other term (step 13)
When the question names a term, or a calendar rule resolved one, an evidence sentence that names only
the other term is not quoted (`mentions_other_term` in `app/generation/extractive.py`).
