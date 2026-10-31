# architecture

How the components fit together and why they are built this way. The handover memo
(`docs/handover-memo.md`) points here for the design; field-level formats are in
`docs/data-dictionary.md`.

## the one idea

**The code decides; the model only phrases.** Every step that can make an answer wrong in a way a
student cannot see (which document version is in force, whether a deadline has passed, which
weekday a date falls on, whether sources disagree, whether to answer at all) is done by code that
can be tested. The local model does two narrow jobs: label the question's intent, and add one to
three explanation sentences that are each checked before a student sees them. If the model is
wrong, slow or down, the system falls back to code-written sentences and verbatim quotes, or to an
honest non-answer.

## offline: documents to index

```
data/sources.json ──fetch──> data/raw/*.pdf|html ──build-calendar──> data/processed/calendar/*.json
     (registry:                     │                                  (24 events, weekdays checked)
      version, authority,           └──ingest──> data/processed/chunks.jsonl (186 passages)
      effective dates)                    │        + quarantine.json (text addressed to the model)
                                          └──first query──> data/processed/embeddings/*.npy
```

- `app/documents/loader.py` extracts text with PyMuPDF and repairs reversed Arabic words
  (1,086 reduced to 4). `normalize.py` gives one search form for Arabic (hamza, ta marbuta, ya).
- `chunker.py` packs regulation and guide text into chunks of about 160 words with page, section
  heading and article number; one chunk per FAQ question and per calendar event. Every chunk carries
  the source's version metadata, and its `source_id`, page and section become the citation.
- `injection.py` keeps passages that address the model ("ignore the instructions…") out of the index.
- Ingest is deterministic: identical input gives byte-identical chunks (sha256 printed and checked
  by `setup.py`).

## online: one question

```
question + as_of date (+ clarification reply)
  │
  1 third-party guard ............ another student's data → STAFF_REVIEW_REQUIRED
  2 intent (model, 17 labels) .... misspelled labels mapped; unknown → OUT_OF_SCOPE
  3 clarification ................ "can I withdraw?" → course / semester / program?   CLARIFICATION_REQUIRED
  4 out of scope ................. after clarification, so a vague withdrawal is never out of scope
  5 retrieval .................... hybrid BM25 + e5 (RRF k=60), only versions in force on as_of
  6 runtime quarantine ........... second check for text addressed to the model
  7 evidence validation .......... currency → relevance → contradiction (authority order) → completeness
  8 rules ........................ calendar deadlines, regulation thresholds, calendar rows, statements
  9 gate ......................... no rule and no passage sharing the question's key terms → INSUFFICIENT_EVIDENCE
 10 compose ...................... rule sentences (code) + model sentences that pass every check,
                                   else verbatim quotes, else INSUFFICIENT_EVIDENCE
 11 escalation ................... decisions, exceptions, personal records → STAFF_REVIEW_REQUIRED
  │
response: status, answer, conditions, required action, sources, date basis, escalation block
```

`app/pipeline/assistant.py` holds this order in one method; each stage is a module that can be
tested alone. The web page (`app/routes.py`) and the CLI (`cli.py ask`) call the same
`Assistant.answer`, so they cannot drift apart.

## decisions and their reasons

| decision | reason |
|---|---|
| `as_of` is an input everywhere; only the interface reads the clock | the same question has different correct answers on different dates; evaluation needs fixed dates; a forwarded answer must show its date basis |
| six statuses, schema-checked | the brief's contract; a refusal must say *why* (missing, conflicting, out of scope, needs staff) so the student knows what to do next |
| authority order regulation > calendar > guide > procedure > FAQ, then effective date | mirrors how the Deanship resolves conflicts; **assumed**, not yet confirmed (`docs/authority-hierarchy.md`) |
| hybrid retrieval, RRF k = 60, 50 candidates each | BM25 finds every Arabic answer in the top 10; embeddings are needed for English questions over Arabic text; hybrid was best overall (Experiment 2). k = 60 is the usual RRF constant, not tuned |
| top 5 passages, at most 3 (700 characters each) sent to the model | keeps the prompt short enough for a 3B model on an 8 GB laptop (`TOP_K`, `GEN_EVIDENCE_LIMIT`, `GEN_EVIDENCE_CHARS` in `config/config.py`); not tuned on the evaluation sets |
| `qwen2.5:3b` through Ollama | chosen to run on the development machine (Intel Mac, 8 GB RAM, CPU only); handles Arabic; out-of-scope F1 0.94 against 0.52 for keywords (Experiment 1). Larger models were not measured |
| `intfloat/multilingual-e5-small` | multilingual (Arabic and English in one space), small enough for CPU, pinned by commit hash |
| deadlines, weekdays and thresholds written by code | phase 8: the model wrote Friday for a Thursday deadline and failed to say a window had closed |
| per-sentence filter, not whole-answer accept/reject | phase 10b: one bad sentence used to sink a good answer, or a good-looking answer hid one bad sentence |
| extractive fallback (verbatim quotes) | when the model text fails, a quote is still grounded and cited; better than nothing, worse than a sentence (quotes can be awkward where extraction damaged the text) |
| escalation shows only code-written text as "confirmed" | a model sentence implied the student met the conditions (found by hand, step 12) |
| clarification checked before out-of-scope | "I want to withdraw" was classified out of scope (v1: E071, E072) |
| committed model cache (SHA-256 of model, digest, parameters, prompt) | reported numbers reproduce exactly and fast (Development Standards 1.5) |
| temperature 0, seed 42 | identical output for identical input (reproducibility 1.00 on every run) |
| Flask, server-rendered page, no JavaScript framework | one page, two languages, works on a phone; nothing to build |
| question text never logged | privacy (`docs/data-handling.md`); escalation logs keep only reason, intent and source ids |

## where to look

| concern | module |
|---|---|
| document registry and version selection | `app/documents/registry.py`, `version_selector.py` |
| retrieval | `app/retrieval/` (`retriever.py` filters by date, `hybrid.py` fuses) |
| evidence validation | `app/evidence/validator.py` and its steps |
| rules | `rules/rule_library.json`, `app/rules/rule_engine.py`, `calendar_rules.py`, `registration_rules.py`, `selection.py`, `event_lookup.py` |
| answer text | `app/generation/` (`rule_sentences.py` code-written, `answer_generator.py` model, `extractive.py` quotes) |
| checks | `app/safety/verifier.py` (whole text), `sentence_filter.py` (each sentence), `escalation.py` |
| evaluation | `app/pipeline/evaluate.py`, `baseline.py`, `ratings.py`; `cli.py evaluate-*` |
| deployment | `Dockerfile` (Hugging Face Space), `docker/` (local two-service run), `setup.py` (bootstrap) |
