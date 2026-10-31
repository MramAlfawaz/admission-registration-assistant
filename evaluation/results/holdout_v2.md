# Experiment 3: holdout_v2

Set: `evaluation/end_to_end/holdout.jsonl`, sha256 `3ee21c4c6cff`, 40 inquiries.
Automatic first-pass labels; see `docs/evaluation.md` for definitions and limits.

| metric | overall | Arabic | English |
|---|---|---|---|
| status accuracy (all six) | 0.95 | 1.0 | 0.875 |
| correct refusal rate | 1.0 | 1.0 | 1.0 |
| correct refusal, exact status | 1.0 | 1.0 | 1.0 |
| false refusal rate | 0.077 | 0.0 | 0.2 |
| answer correct when answered | 0.708 | 0.688 | 0.75 |
| end-to-end correct | 0.775 | 0.792 | 0.75 |
| wrong answers shown to a student | 7 | 5 | 2 |
| grounded claim rate (judged claims) | 0.857 | 0.892 | 0.6 |
| unsupported claim rate (judged claims) | 0.143 | 0.108 | 0.4 |
| grounded rate, model sentences only | 0.812 | 0.867 | 0.0 |
| claims needing human review | 12 | 0 | 12 |
| citation accuracy (judged citations) | 1.0 | 1.0 | 1.0 |
| self-service rate | 0.425 | 0.458 | 0.375 |

Response time (s): median 0.05, p90 0.09, max 42.89. Reproducible on repeat: 1.0.
Answer modes: {'generated': 20, 'extractive': 4, 'templated': 12, 'escalated': 4}

## confusion (rows expected, columns returned)

| expected \ returned | ANSWERABLE | CLARIFICATIO | INSUFFICIENT | CONFLICTING_ | OUT_OF_SCOPE | STAFF_REVIEW |
|---|---|---|---|---|---|---|
| ANSWERABLE | 24 | 0 | 2 | 0 | 0 | 0 |
| CLARIFICATION_REQUIRED | 0 | 4 | 0 | 0 | 0 | 0 |
| INSUFFICIENT_EVIDENCE | 0 | 0 | 3 | 0 | 0 | 0 |
| CONFLICTING_EVIDENCE | 0 | 0 | 0 | 0 | 0 | 0 |
| OUT_OF_SCOPE | 0 | 0 | 0 | 0 | 3 | 0 |
| STAFF_REVIEW_REQUIRED | 0 | 0 | 0 | 0 | 0 | 4 |

## every incorrect inquiry

| id | lang | expected | returned | mode | problem |
|---|---|---|---|---|---|
| H002 | ar | ANSWERABLE | ANSWERABLE | generated | required fact missing |
| H005 | ar | ANSWERABLE | ANSWERABLE | generated | required fact missing |
| H006 | ar | ANSWERABLE | ANSWERABLE | generated | required fact missing |
| H010 | ar | ANSWERABLE | ANSWERABLE | generated | required fact missing |
| H016 | ar | ANSWERABLE | ANSWERABLE | generated | required fact missing |
| H018 | en | ANSWERABLE | ANSWERABLE | generated | required fact missing |
| H019 | en | ANSWERABLE | ANSWERABLE | generated | required fact missing |
| H021 | en | ANSWERABLE | INSUFFICIENT_EVIDENCE | templated | wrong status |
| H024 | en | ANSWERABLE | INSUFFICIENT_EVIDENCE | templated | wrong status |
