# context

A one-page orientation for anyone (or any coding assistant) about to change this repository.
Details: `README.md` (install, results), `docs/architecture.md` (design), `docs/handover-memo.md`
(state, limitations, how to extend).

## what this is
An Arabic/English assistant for the NAUSS Deanship of Admission and Registration that answers only
from six approved public documents, cites them, states the date it applies to, and refers to staff
whenever it cannot answer safely. Project 5A, Data Science course; governed by the project brief and
the Development Standards.

## rules that must not be broken
- **The code decides, the model phrases.** Dates, weekdays, open/closed, thresholds, document versions,
  conflicts and the decision to answer are code. Never let model text decide any of them.
- **`as_of` is always an input.** Only `app/routes.py` reads today's date.
- **Six statuses only** (`app/schemas/answer.py`); every response is schema-checked.
- **Checks can only remove text**, never make an answer more confident. New checks go in
  `app/safety/` with a test built from the real output that showed the problem.
- **No silent fallback**: a model that does not match `models.lock` stops the system.
- **Never log the question text**; never commit runtime data (`data/raw`, `data/processed`, logs).
- **Frozen evaluation sets are never edited.** A corrected set is a new version, reported beside the old.
- **Report every result, including negative ones**, and say when a fix was informed by a set (optimistic).
- Settings only in `config/config.py`; prompts only in `prompts/` as new versioned files.

## where things are
`app/pipeline/assistant.py` holds the stage order. Domain modules: `documents`, `intent`, `retrieval`,
`evidence`, `rules`, `generation`, `safety`. Everything runs from `cli.py`; `app.py` (development) and
`wsgi.py` (production) serve the page.

## before you commit
`python -m pytest -q` (all pass, no network, no Ollama needed). If behaviour changed, re-run
`evaluate-e2e` on both sets and `evaluate-adversarial`, save under a new name, and update the README.
