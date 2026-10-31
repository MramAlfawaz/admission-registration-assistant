# data handling

Required by the brief (Section 12): what is logged and kept, decided before logging was built.

## what the system receives
A question (free text), the date it is about, and optionally a clarification reply. **It does not
receive and never looks up student records.** Questions that need a student's own record are
escalated (`personal_record`); requests for another student's data are refused and escalated
(`third_party`).

## what is logged
| log | contents | question text? | where |
|---|---|---|---|
| application log | timestamp, level, module, message (statuses, timings, warnings) | **no** | standard error; not written to the repository (`*.log`, `logs/` ignored) |
| escalation log | logged_at, as_of, reason code, intent, source ids | **no** | `data/processed/escalations.jsonl` (ignored by git) |
| evaluation escalation logs | same fields | **no** | `evaluation/results/*_escalations.jsonl` (synthetic questions only) |
| model call cache | model, digest, parameters, prompt, response, seconds | **yes, inside the prompt** | `data/cache/llm/` |

## the model call cache
Every model call is cached under a SHA-256 key (Development Standards 1.5) so reported numbers can be
reproduced. The prompt contains the question. Decisions:
- the **committed** cache contains only calls made for the synthetic evaluation sets and development;
  it holds no real student question
- a **deployed** instance must set `CACHE_DIR` to a location outside the repository that is never
  committed, and delete entries older than 30 days. Both Docker images do this (`docker/start.sh`):
  the cache lives in a runtime folder of the container (`/home/user/runtime/cache` on the Space),
  starts from the committed evaluation cache, has entries older than 30 days deleted daily, and is
  lost when the container restarts
- no IP addresses, names or identifiers are stored anywhere by the application

## retention
Application and escalation logs: 30 days, then deleted. Evaluation results: kept in the repository
as evidence for the reported numbers (synthetic questions only).

## evaluation data
All evaluation questions are **synthetic**, written by the developer from the public documents. No
anonymised inquiry log was available (brief, Phase 0). No personal data is committed: the only
student identifiers in the repository are invented test values (for example `441234567` in the
adversarial set, used to check that the system refuses).

## source documents
Public documents from nauss.edu.sa. Raw files are not committed (`data/raw/` ignored); `python cli.py
fetch` restores them from the URLs in `data/sources.json`.

## models
Both models run locally (Ollama `qwen2.5:3b`, `intfloat/multilingual-e5-small`). No question or
document is sent to an external service.
