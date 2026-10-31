# Experiment 3: e2e_smoke

Set: `evaluation/end_to_end/inquiries.jsonl`, sha256 `1d187245c016`, 5 inquiries.
Automatic first-pass labels; see `docs/evaluation.md` for definitions and limits.

| metric | overall | Arabic | English |
|---|---|---|---|
| status accuracy (all six) | 1.0 | 1.0 | None |
| correct refusal rate | None | None | None |
| correct refusal, exact status | None | None | None |
| false refusal rate | 0.0 | 0.0 | None |
| answer correct when answered | 1.0 | 1.0 | None |
| end-to-end correct | 1.0 | 1.0 | None |
| wrong answers shown to a student | 0 | 0 | 0 |
| grounded claim rate (judged claims) | 0.7 | 0.7 | None |
| unsupported claim rate (judged claims) | 0.3 | 0.3 | None |
| grounded rate, model sentences only | 0.833 | 0.833 | None |
| claims needing human review | 0 | 0 | 0 |
| citation accuracy (judged citations) | 1.0 | 1.0 | None |
| self-service rate | 1.0 | 1.0 | None |

Response time (s): median 24.8, p90 36.84, max 55.06. Reproducible on repeat: 1.0.
Answer modes: {'generated': 3, 'extractive': 2}

## confusion (rows expected, columns returned)

| expected \ returned | ANSWERABLE | CLARIFICATIO | INSUFFICIENT | CONFLICTING_ | OUT_OF_SCOPE | STAFF_REVIEW |
|---|---|---|---|---|---|---|
| ANSWERABLE | 5 | 0 | 0 | 0 | 0 | 0 |
| CLARIFICATION_REQUIRED | 0 | 0 | 0 | 0 | 0 | 0 |
| INSUFFICIENT_EVIDENCE | 0 | 0 | 0 | 0 | 0 | 0 |
| CONFLICTING_EVIDENCE | 0 | 0 | 0 | 0 | 0 | 0 |
| OUT_OF_SCOPE | 0 | 0 | 0 | 0 | 0 | 0 |
| STAFF_REVIEW_REQUIRED | 0 | 0 | 0 | 0 | 0 | 0 |

## every incorrect inquiry

| id | lang | expected | returned | mode | problem |
|---|---|---|---|---|---|
