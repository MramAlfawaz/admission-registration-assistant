# Experiment 3: e2e_v1

Set: `evaluation/end_to_end/inquiries.jsonl`, sha256 `1d187245c016`, 100 inquiries.
Automatic first-pass labels; see `docs/evaluation.md` for definitions and limits.

| metric | overall | Arabic | English |
|---|---|---|---|
| status accuracy (all six) | 0.87 | 0.933 | 0.775 |
| correct refusal rate | 0.933 | 0.941 | 0.923 |
| correct refusal, exact status | 0.867 | 0.882 | 0.846 |
| false refusal rate | 0.129 | 0.047 | 0.259 |
| answer correct when answered | 0.656 | 0.683 | 0.6 |
| end-to-end correct | 0.66 | 0.717 | 0.575 |
| wrong answers shown to a student | 23 | 14 | 9 |
| grounded claim rate (judged claims) | 0.75 | 0.757 | 0.667 |
| unsupported claim rate (judged claims) | 0.25 | 0.243 | 0.333 |
| grounded rate, model sentences only | 0.764 | 0.791 | 0.0 |
| claims needing human review | 33 | 0 | 33 |
| citation accuracy (judged citations) | 0.987 | 0.985 | 1.0 |
| self-service rate | 0.4 | 0.467 | 0.3 |

Response time (s): median 0.06, p90 31.71, max 78.23. Reproducible on repeat: 1.0.
Answer modes: {'generated': 53, 'extractive': 10, 'templated': 28, 'escalated': 9}

## confusion (rows expected, columns returned)

| expected \ returned | ANSWERABLE | CLARIFICATIO | INSUFFICIENT | CONFLICTING_ | OUT_OF_SCOPE | STAFF_REVIEW |
|---|---|---|---|---|---|---|
| ANSWERABLE | 61 | 0 | 8 | 0 | 0 | 1 |
| CLARIFICATION_REQUIRED | 0 | 8 | 0 | 0 | 2 | 0 |
| INSUFFICIENT_EVIDENCE | 1 | 0 | 5 | 0 | 0 | 0 |
| CONFLICTING_EVIDENCE | 0 | 0 | 0 | 0 | 0 | 0 |
| OUT_OF_SCOPE | 1 | 0 | 0 | 0 | 5 | 0 |
| STAFF_REVIEW_REQUIRED | 0 | 0 | 0 | 0 | 0 | 8 |

## every incorrect inquiry

| id | lang | expected | returned | mode | problem |
|---|---|---|---|---|---|
| E008 | ar | ANSWERABLE | INSUFFICIENT_EVIDENCE | templated | wrong status |
| E010 | en | ANSWERABLE | INSUFFICIENT_EVIDENCE | templated | wrong status |
| E012 | en | ANSWERABLE | INSUFFICIENT_EVIDENCE | templated | wrong status |
| E013 | en | ANSWERABLE | INSUFFICIENT_EVIDENCE | templated | wrong status |
| E014 | en | ANSWERABLE | INSUFFICIENT_EVIDENCE | templated | wrong status |
| E017 | ar | ANSWERABLE | ANSWERABLE | generated | required fact missing |
| E018 | ar | ANSWERABLE | ANSWERABLE | generated | required fact missing |
| E019 | en | ANSWERABLE | ANSWERABLE | generated | required fact missing |
| E023 | ar | ANSWERABLE | ANSWERABLE | generated | required fact missing |
| E024 | en | ANSWERABLE | ANSWERABLE | generated | required fact missing |
| E026 | ar | ANSWERABLE | ANSWERABLE | generated | required fact missing |
| E028 | ar | ANSWERABLE | ANSWERABLE | generated | required fact missing |
| E030 | en | ANSWERABLE | INSUFFICIENT_EVIDENCE | templated | wrong status |
| E032 | en | ANSWERABLE | ANSWERABLE | generated | required fact missing |
| E035 | ar | ANSWERABLE | ANSWERABLE | generated | required fact missing |
| E036 | en | ANSWERABLE | ANSWERABLE | generated | required fact missing |
| E037 | en | ANSWERABLE | ANSWERABLE | generated | required fact missing |
| E045 | ar | ANSWERABLE | ANSWERABLE | generated | required fact missing |
| E048 | en | ANSWERABLE | INSUFFICIENT_EVIDENCE | templated | wrong status |
| E050 | ar | ANSWERABLE | ANSWERABLE | generated | required fact missing |
| E051 | en | ANSWERABLE | ANSWERABLE | extractive | required fact missing |
| E052 | ar | ANSWERABLE | ANSWERABLE | generated | required fact missing |
| E053 | ar | ANSWERABLE | ANSWERABLE | extractive | required fact missing |
| E058 | ar | ANSWERABLE | STAFF_REVIEW_REQUIRED | escalated | wrong status |
| E059 | ar | ANSWERABLE | ANSWERABLE | generated | required fact missing |
| E061 | ar | ANSWERABLE | ANSWERABLE | generated | required fact missing |
| E062 | en | ANSWERABLE | ANSWERABLE | generated | required fact missing |
| E064 | ar | ANSWERABLE | ANSWERABLE | generated | required fact missing |
| E065 | en | ANSWERABLE | ANSWERABLE | generated | required fact missing |
| E070 | en | ANSWERABLE | INSUFFICIENT_EVIDENCE | templated | wrong status |
| E071 | ar | CLARIFICATION_REQUIRED | OUT_OF_SCOPE | templated | wrong status |
| E072 | en | CLARIFICATION_REQUIRED | OUT_OF_SCOPE | templated | wrong status |
| E093 | ar | OUT_OF_SCOPE | ANSWERABLE | generated | wrong status |
| E098 | en | INSUFFICIENT_EVIDENCE | ANSWERABLE | generated | wrong status |
