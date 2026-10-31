# Experiment 3: holdout_before

Set: `evaluation/end_to_end/holdout.jsonl`, sha256 `3ee21c4c6cff`, 40 inquiries.
Automatic first-pass labels; see `docs/evaluation.md` for definitions and limits.

| metric | overall | Arabic | English |
|---|---|---|---|
| status accuracy (all six) | 0.85 | 0.875 | 0.812 |
| correct refusal rate | 0.857 | 0.75 | 1.0 |
| correct refusal, exact status | 0.786 | 0.75 | 0.833 |
| false refusal rate | 0.115 | 0.062 | 0.2 |
| answer correct when answered | 0.652 | 0.667 | 0.625 |
| end-to-end correct | 0.65 | 0.667 | 0.625 |
| wrong answers shown to a student | 10 | 7 | 3 |
| grounded claim rate (judged claims) | 0.8 | 0.795 | 1.0 |
| unsupported claim rate (judged claims) | 0.2 | 0.205 | 0.0 |
| grounded rate, model sentences only | 0.778 | 0.778 | None |
| claims needing human review | 15 | 0 | 15 |
| citation accuracy (judged citations) | 1.0 | 1.0 | 1.0 |
| self-service rate | 0.375 | 0.417 | 0.312 |

Response time (s): median 32.41, p90 42.88, max 68.02. Reproducible on repeat: 1.0.
Answer modes: {'generated': 22, 'extractive': 3, 'escalated': 3, 'templated': 12}

## confusion (rows expected, columns returned)

| expected \ returned | ANSWERABLE | CLARIFICATIO | INSUFFICIENT | CONFLICTING_ | OUT_OF_SCOPE | STAFF_REVIEW |
|---|---|---|---|---|---|---|
| ANSWERABLE | 23 | 0 | 2 | 0 | 0 | 1 |
| CLARIFICATION_REQUIRED | 0 | 4 | 0 | 0 | 0 | 0 |
| INSUFFICIENT_EVIDENCE | 1 | 0 | 2 | 0 | 0 | 0 |
| CONFLICTING_EVIDENCE | 0 | 0 | 0 | 0 | 0 | 0 |
| OUT_OF_SCOPE | 0 | 0 | 0 | 0 | 3 | 0 |
| STAFF_REVIEW_REQUIRED | 1 | 0 | 1 | 0 | 0 | 2 |

## every incorrect inquiry

| id | lang | expected | returned | mode | problem |
|---|---|---|---|---|---|
| H002 | ar | ANSWERABLE | ANSWERABLE | generated | required fact missing |
| H005 | ar | ANSWERABLE | ANSWERABLE | generated | required fact missing |
| H006 | ar | ANSWERABLE | ANSWERABLE | generated | required fact missing |
| H009 | ar | ANSWERABLE | STAFF_REVIEW_REQUIRED | escalated | wrong status |
| H010 | ar | ANSWERABLE | ANSWERABLE | generated | required fact missing |
| H016 | ar | ANSWERABLE | ANSWERABLE | generated | required fact missing |
| H018 | en | ANSWERABLE | ANSWERABLE | generated | required fact missing |
| H019 | en | ANSWERABLE | ANSWERABLE | generated | required fact missing |
| H021 | en | ANSWERABLE | INSUFFICIENT_EVIDENCE | templated | wrong status |
| H023 | en | ANSWERABLE | ANSWERABLE | generated | required fact missing |
| H024 | en | ANSWERABLE | INSUFFICIENT_EVIDENCE | templated | wrong status |
| H031 | ar | STAFF_REVIEW_REQUIRED | ANSWERABLE | generated | wrong status |
| H034 | en | STAFF_REVIEW_REQUIRED | INSUFFICIENT_EVIDENCE | templated | wrong status |
| H040 | ar | INSUFFICIENT_EVIDENCE | ANSWERABLE | generated | wrong status |
