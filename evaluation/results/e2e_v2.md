# Experiment 3: e2e_v2

Set: `evaluation/end_to_end/inquiries.jsonl`, sha256 `1d187245c016`, 100 inquiries.
Automatic first-pass labels; see `docs/evaluation.md` for definitions and limits.

| metric | overall | Arabic | English |
|---|---|---|---|
| status accuracy (all six) | 0.95 | 0.967 | 0.925 |
| correct refusal rate | 1.0 | 1.0 | 1.0 |
| correct refusal, exact status | 0.967 | 0.941 | 1.0 |
| false refusal rate | 0.057 | 0.023 | 0.111 |
| answer correct when answered | 0.803 | 0.833 | 0.75 |
| end-to-end correct | 0.82 | 0.85 | 0.775 |
| wrong answers shown to a student | 13 | 7 | 6 |
| grounded claim rate (judged claims) | 0.772 | 0.757 | 0.875 |
| unsupported claim rate (judged claims) | 0.228 | 0.243 | 0.125 |
| grounded rate, model sentences only | 0.775 | 0.786 | 0.0 |
| claims needing human review | 30 | 0 | 30 |
| citation accuracy (judged citations) | 0.98 | 0.975 | 1.0 |
| self-service rate | 0.53 | 0.583 | 0.45 |

Response time (s): median 0.05, p90 0.18, max 41.99. Reproducible on repeat: 1.0.
Answer modes: {'extractive': 21, 'generated': 45, 'templated': 26, 'escalated': 8}

## confusion (rows expected, columns returned)

| expected \ returned | ANSWERABLE | CLARIFICATIO | INSUFFICIENT | CONFLICTING_ | OUT_OF_SCOPE | STAFF_REVIEW |
|---|---|---|---|---|---|---|
| ANSWERABLE | 66 | 0 | 4 | 0 | 0 | 0 |
| CLARIFICATION_REQUIRED | 0 | 10 | 0 | 0 | 0 | 0 |
| INSUFFICIENT_EVIDENCE | 0 | 0 | 6 | 0 | 0 | 0 |
| CONFLICTING_EVIDENCE | 0 | 0 | 0 | 0 | 0 | 0 |
| OUT_OF_SCOPE | 0 | 0 | 1 | 0 | 5 | 0 |
| STAFF_REVIEW_REQUIRED | 0 | 0 | 0 | 0 | 0 | 8 |

## every incorrect inquiry

| id | lang | expected | returned | mode | problem |
|---|---|---|---|---|---|
| E008 | ar | ANSWERABLE | INSUFFICIENT_EVIDENCE | templated | wrong status |
| E017 | ar | ANSWERABLE | ANSWERABLE | generated | required fact missing |
| E018 | ar | ANSWERABLE | ANSWERABLE | generated | required fact missing |
| E019 | en | ANSWERABLE | INSUFFICIENT_EVIDENCE | templated | wrong status |
| E023 | ar | ANSWERABLE | ANSWERABLE | generated | required fact missing |
| E024 | en | ANSWERABLE | ANSWERABLE | generated | required fact missing |
| E026 | ar | ANSWERABLE | ANSWERABLE | generated | required fact missing |
| E028 | ar | ANSWERABLE | ANSWERABLE | generated | required fact missing |
| E032 | en | ANSWERABLE | ANSWERABLE | generated | required fact missing |
| E035 | ar | ANSWERABLE | ANSWERABLE | generated | required fact missing |
| E036 | en | ANSWERABLE | ANSWERABLE | generated | required fact missing |
| E037 | en | ANSWERABLE | ANSWERABLE | extractive | required fact missing |
| E045 | ar | ANSWERABLE | ANSWERABLE | generated | required fact missing |
| E048 | en | ANSWERABLE | INSUFFICIENT_EVIDENCE | templated | wrong status |
| E062 | en | ANSWERABLE | ANSWERABLE | generated | required fact missing |
| E065 | en | ANSWERABLE | ANSWERABLE | generated | required fact missing |
| E070 | en | ANSWERABLE | INSUFFICIENT_EVIDENCE | templated | wrong status |
| E093 | ar | OUT_OF_SCOPE | INSUFFICIENT_EVIDENCE | templated | wrong status |
