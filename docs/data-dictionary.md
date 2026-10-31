# data dictionary

Every data structure the system reads or writes, with its fields. Shared identifiers follow the brief
(Section 13): `source_id`, `chunk_id`, `term_id`, `program_id` (not yet used), `student_id` (never stored).

## `data/sources.json`: source registry (one object per document version)
| field | type | meaning |
|---|---|---|
| source_id | string | stable id, for example `CALENDAR-1448` |
| title | string | document title as published |
| document_type | enum | regulation, calendar, program_requirements, procedure, faq |
| authority_level | int | 1 (highest) to 5, see `docs/authority-hierarchy.md` |
| version | string | for example `1448` |
| effective_from / effective_to | date / null | inclusive dates the version is in force; `null` = open |
| status | enum | approved, superseded |
| supersedes | string / null | source_id this version replaces |
| language | enum | ar, en |
| dates_assumed | bool | true when the developer set dates the document does not state |
| url, filename | string | where `fetch` downloads it and the local file name in `data/raw/` |

## `data/processed/chunks.jsonl`: retrievable passages (built by `ingest`)
| field | type | meaning |
|---|---|---|
| chunk_id | string | `<source_id>#<nnn>`, positional |
| source_id, document_type, authority_level, version, status, effective_from, effective_to, language, title | | copied from the source |
| page, page_end | int | PDF pages the passage spans |
| section | string | nearest heading, or `row N` for calendar rows |
| article | string / null | regulation article number when stated |
| event_code, term_id | string / null | calendar rows only, for example `SEMESTER_WITHDRAWAL_DEADLINE`, `1448-T1` |
| text | string | cleaned passage text (display form) |

`data/processed/quarantine.json`: passages kept out of the index because they address the model
(`chunk_id`, `source_id`, `signals`).

## `data/processed/calendar/<source_id>.json`: calendar events (built by `build-calendar`)
`row`, `event` (Arabic name), `code`, `term_id`, `day` (weekday text as printed), `date_start`,
`date_end`, `hijri_start`, `hijri_end`, `source_id`, `section`.

## `rules/rule_library.json`: rule library
`rule_id`, `title`, `kind` (calendar, regulation, eligibility), `inputs`, `outputs`, `condition`,
`sources` (source_id and section), `effective_from`, `effective_to`, `tests`; calendar rules add
`event_code`, `comparison`, `term_basis` (current or upcoming); threshold rules add `function`.

## response (`app/schemas/answer.py`)
| field | type | meaning |
|---|---|---|
| status | enum | ANSWERABLE, CLARIFICATION_REQUIRED, INSUFFICIENT_EVIDENCE, CONFLICTING_EVIDENCE, OUT_OF_SCOPE, STAFF_REVIEW_REQUIRED |
| intent | string | one of the 17 intents (`docs/intent-taxonomy.md`) |
| language | enum | ar, en (the answer's language) |
| as_of | date | the date the question is about (an input, never the clock) |
| answer | string | rule sentences first, then checked model sentences or quoted evidence |
| conditions | list of strings | conditions written in the evidence |
| required_action | string | what to do, only when the evidence says so |
| rule_outputs | list | `rule_id`, `output`, `details` for each rule used |
| sources | list | `source_id`, `chunk_id`, `page`, `section` of every passage or rule source used |
| date_basis | string | "based on approved information available on <as_of>" |
| clarification | object / null | the question asked and its options |
| escalation | object / null | `reason`, `reason_code`, `confirmed`, `evidence`, `next_step` |
| verified | bool | set only by the pipeline after the checks |
| _trace | object | internal: stages, retrieved ids, dropped sentences; never shown to a student |

## evaluation sets
| file | fields |
|---|---|
| `evaluation/intent/questions.jsonl` | id, question, language, intent, ambiguous, expected_missing, origin, split |
| `evaluation/retrieval/gold.jsonl` | id, question, language, as_of, intent, evidence (groups of chunk ids), origin |
| `evaluation/version_selection/cases.json` | id, as_of, family (for example PROGRAMS-GUIDE), expected source_id |
| `evaluation/conflicts/planted.jsonl` | id, description, intent, question, as_of, sources (metadata of the planted documents), chunks (planted passages), expected (conflict, winner, status) |
| `evaluation/end_to_end/inquiries.jsonl`, `holdout.jsonl` | id, question, language, as_of, category, expected_status, must_contain (groups: all must match, any alternative), must_not_contain, clarify, origin, note |
| `evaluation/adversarial/cases.jsonl` | id, kind, language, question, as_of, acceptable_statuses, must_contain, must_not_contain, require_sources, forbidden_sources, inject, expect_flag |

## logs and caches
- escalation log (`data/processed/escalations.jsonl`): logged_at, as_of, reason, intent, sources
- model cache (`data/cache/llm/<sha256>.json`): model, digest, params, prompt, response, seconds
