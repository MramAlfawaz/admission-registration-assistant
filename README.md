---
title: Admission and Registration Assistant
emoji: 🎓
colorFrom: green
colorTo: gray
sdk: docker
app_port: 7860
pinned: false
short_description: Answers from approved NAUSS admission documents
---

# admission-registration-assistant

An assistant for the Admission and Registration department of Naif Arab University
for Security Sciences (NAUSS). It answers student questions in Arabic and English
**only from approved institutional documents**, cites the document and section it
used, and refers the student to staff when the evidence is missing, contradictory,
or the question needs an official decision.

Project 5A, Data Science course. Built to the project brief and the Development
Standards document.

> **Status:** all 13 phases built. Remaining before handover: the public demo's first build, the
> Experiment 5 team rating and a test by someone outside the team (`docs/handover-memo.md`, section 1).
> The block at the top of this file is read by Hugging Face Spaces (the public demo), not by GitHub.
> The assistant answers end to end from the command line: it classifies the question,
> asks for clarification when needed, retrieves passages in force on the question's
> date, validates them, applies the rule library, writes the answer with fixed rule
> sentences plus checked model sentences, and escalates decisions to staff.
>
> **First full evaluation (2026-10-31): 66 of 100 inquiries fully correct, 18 answers
> with a wrong or missing fact. Not yet safe for students.** The failures are analysed
> by cause in `docs/e2e-v1-failures.md`. Fixes by cause raised the same 100 inquiries to
> 0.95 status accuracy (optimistic: the fixes were written after seeing them) but did **not**
> improve a held-out set frozen before the fixes (status accuracy 0.85 before, 0.825 after,
> 10 wrong answers both times). Adversarial cases: 17/17 after the fixes.

---

## what it produces today

| output | quantity |
|---|---|
| official source documents registered | 6 (4 PDF, 2 web pages) |
| retrievable chunks built from them | 186, identical on every run (sha256 `9e6394386f2f`) |
| structured academic-calendar events | 24, every weekday checked against its date |
| intent labels | 17 |
| labelled evaluation questions | 155 (87 Arabic, 64 English, 4 mixed) |
| labelled version-selection cases | 15, all passing |
| retrieval gold questions | 64 (39 Arabic, 25 English), each with a reference date |
| Arabic retrieval, hybrid | recall@5 0.974, recall@10 1.000 |
| passages retrieved from a version not in force | 0 |
| planted contradictions detected | 20 cases: detection 1.0, false positives 0.0, resolution 1.0 |
| rules in the rule library | 13 (5 calendar, 6 regulation, 2 eligibility), each with boundary tests |
| answer statuses | 6, every response schema-checked |
| frozen end-to-end inquiries | 100 (60 Arabic, 40 English), 30 with a non-answer as the correct result |
| adversarial cases | 17, every case in brief Section 11 |
| end-to-end v1 (first run) | 66/100 fully correct; correct refusal 0.93, false refusal 0.13 |
| adversarial v1 (first run) | 12/17 passed; all 3 planted-document attacks blocked |
| held-out inquiries (frozen before fixes) | 40: status accuracy 0.85 before, 0.825 after the step 11b fixes |
| Experiment 4: same model with no retrieval | 14/100 correct and 79 wrong answers shown, against 82/100 and 13 for the assistant |
| response time (no cached calls, 8 GB Intel Mac) | median 32 s; answered 35 s, refusals 2 s |
| automated tests | 206 passing |
| Arabic words repaired in PDF extraction | 1,086 reversed words reduced to 4 |

---

## installation

Tested on macOS 15 (Intel Core i5, 8 GB RAM). Each step is followed by a check.

**0. prerequisites:** Python 3.11.9, Git, and [Ollama](https://ollama.com/download).
```bash
python3.11 --version   # Python 3.11.9
git --version
ollama --version
```
Python 3.11 is required, not 3.12 or 3.13: the last PyTorch build for Intel Macs
(2.2.2) supports Python up to 3.12, and the project is pinned to 3.11.9.

**1. clone the repository**
```bash
git clone https://github.com/MramAlfawaz/admission-registration-assistant.git
cd admission-registration-assistant
```
Check: `ls` shows `cli.py`, `app/`, `data/sources.json`.

**2. create and activate the virtual environment**
```bash
python3.11 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
```
Check: `python --version` prints `Python 3.11.9`. If Anaconda is installed, run
`conda deactivate` first so it does not override the environment.

**3. install the pinned packages**
```bash
pip install -r requirements.txt
```
Check:
```bash
python -c "import numpy, torch, fitz, flask; print(numpy.__version__, torch.__version__)"
# 1.26.4 2.2.2
```

**4. install the local model**
```bash
ollama pull qwen2.5:3b
```
Check: `ollama list` shows `qwen2.5:3b` with ID `357c53fb659c`.

**5. bootstrap** (Ollama must be running)
```bash
python setup.py
```
It checks the interpreter and every package pin, creates `.env` from `.env.example`, downloads the 6
documents, builds the calendar and the chunks, downloads the pinned embedding model (about 470 MB, once)
and checks the generation model against `models.lock`. It stops with an instruction at the first problem.
Check: the last line is `bootstrap passed`, after `step 3 ok: 186 chunks, sha256 9e6394386f2f (as measured)`.

The same steps by hand: `cp .env.example .env`, `python cli.py fetch`, `python cli.py build-calendar`,
`python cli.py ingest`, `python cli.py check-model`.

**6. run the tests**
```bash
python -m pytest -q
```
Check: `206 passed`.

**7. ask one question from the command line**
```bash
python cli.py ask "متى آخر موعد للاعتذار عن الفصل الدراسي الأول؟" --as-of 2026-10-14
```
Check: status `ANSWERABLE`, an answer stating Thursday 2026-11-19 and that the period is still open, and the
calendar row as source.

**8. open the student page**
```bash
python app.py
```
Open http://localhost:5001. The first question takes longer while the models load (about 30 s per
answer after that on the development Mac; instant for questions already in the cache).

**Windows:** use `py -3.11 -m venv .venv` and `.venv\Scripts\activate`; the other commands are the same.
Windows has not been tested end to end.

**Check a fresh clone in one command** (clones into a temporary folder, installs, bootstraps, runs the tests
and reproduces the held-out results from the committed cache; needs Ollama running):
```bash
bash scripts/clean_install_check.sh
```

### running with Docker
Needs only Docker; Ollama runs in its own container.
```bash
docker compose -f docker/docker-compose.yml up --build
```
Open http://localhost:5001. The first build downloads about 3 GB (Python packages, documents, both models).

### public demo (Hugging Face Space)
The root `Dockerfile` builds one container with the app and Ollama for a free CPU Space (port 7860).
To publish:
0. create a Hugging Face account and a write token (Settings, Access Tokens)
1. create a new Space: SDK **Docker**, template **Blank**, hardware **CPU basic**
2. push a single snapshot of the current files (the Space refuses old commits that held binary files):
```bash
git remote add space https://huggingface.co/spaces/<user>/<space-name>
git push --force space "$(git commit-tree 'HEAD^{tree}' -m 'Deploy snapshot')":refs/heads/main
```
   (user name: your Hugging Face name; password: the write token)
3. follow the build log on the Space page; the build pulls the model and runs `python setup.py`
Check: the Space shows the student page; `/health` returns `{"results": [{"status": "ok"}], "errors": []}`.
Answers are slower than on a laptop (a shared CPU), and the first one after the Space wakes loads the models.

---

## commands

| command | what it does |
|---|---|
| `python cli.py fetch` | downloads every source in `data/sources.json` into `data/raw/`, skipping files already present |
| `python cli.py peek` | writes the extracted text of each source to `data/processed/peek/` for inspection by eye |
| `python cli.py build-calendar` | parses each calendar into structured events in `data/processed/calendar/` |
| `python cli.py ingest` | chunks all sources into `data/processed/chunks.jsonl` |
| `python cli.py add-source ...` | registers a new document version without code changes (see below) |
| `python cli.py check-model` | verifies the installed model against `models.lock` |
| `python cli.py evaluate-intent --method keyword\|llm --split dev\|test\|all` | scores an intent classifier and saves results to `evaluation/results/` |
| `python cli.py evaluate-retrieval --method bm25\|embeddings\|hybrid\|all` | scores retrieval on the gold set and saves results to `evaluation/results/` |
| `python cli.py search "question" --as-of YYYY-MM-DD` | shows the top passages for one question, searching only versions in force on that date |
| `python cli.py evaluate-conflicts` | scores evidence validation on the planted contradictions |
| `python cli.py conflict-report` | lists conflicts met while answering the gold questions, for the department |
| `python cli.py rule RULE-CAL-01 --as-of YYYY-MM-DD [--term 1448-T1] [--input k=v]` | runs one rule on a date |
| `python cli.py rules-doc` | rewrites `docs/rules.md` from the rule library |
| `python cli.py ask "question" --as-of YYYY-MM-DD [--clarify withdrawal_scope=semester]` | answers one question end to end and prints the response and its trace |
| `python cli.py generate-sample --n 10 \| --file smoke.jsonl --out NAME` | runs a sample end to end and checks schema and expectations |
| `python cli.py evaluate-e2e --out NAME [--set inquiries\|holdout] [--limit N]` | Experiment 3 on a frozen set (refuses to run if the set changed) |
| `python cli.py evaluate-no-retrieval --out NAME --compare E2E_RESULTS` | Experiment 4: the same model with no retrieval, compared with the assistant |
| `python cli.py make-exp5` | Experiment 5: writes `evaluation/experiment5/rating_sheet.csv` and `claim_review.csv` to fill in |
| `python cli.py score-ratings` / `score-claims` | Experiment 5: summarises the filled sheets |
| `python cli.py efficiency-report` | Experiment 5: response time from an uncached run, and self-service rate |
| `python app.py` | the student page on http://localhost:5001; `POST /api/ask` for JSON |
| `python cli.py evaluate-adversarial --out adversarial_v1` | runs the 17 adversarial cases |
| `python cli.py compare-runs REFERENCE RUN` | checks two `evaluate-e2e` results are identical inquiry by inquiry (status, correctness, answer, escalation) |
| `python setup.py [--skip-llm]` | bootstrap: pins, `.env`, documents, chunks, embedding model, model check |
| `bash scripts/clean_install_check.sh` | fresh clone → install → bootstrap → tests → reproduce `holdout_v4` |

### adding a new document version
When the department publishes a new calendar or guide:
```bash
python cli.py add-source --file ~/Downloads/calendar-1449.pdf \
  --source-id CALENDAR-1449 --title "التقويم الأكاديمي 1449-1450هـ" \
  --type calendar --authority 2 --version 1449 \
  --effective-from 2027-08-22 --supersedes CALENDAR-1448 \
  --url https://nauss.edu.sa/ar/academic-programmes/Documents/AcademicCalendar.pdf
python cli.py ingest
```
The previous version is closed the day before the new one starts and kept, so
questions about past dates still use the rules that applied then.

---

## repository layout

```
app/
  documents/   loader, normalize, calendar_parser, chunker, version_selector, registry, ingest, injection
  intent/      taxonomy, language, keyword_baseline, llm_classifier, context_extractor, ambiguity, evaluate
  retrieval/   tokenize, bm25, embeddings, hybrid, retriever, evaluate, factory
  evidence/    currency_checker, relevance, subject, facts, contradiction, completeness, validator, evaluate
  rules/       calendar_rules, event_lookup, rule_engine, registration_rules, selection
  generation/  answer_generator, templates, rule_sentences, extractive
  safety/      verifier, sentence_filter, escalation
  schemas/     answer (the six statuses and the response fields)
  pipeline/    assistant (the fixed stage order), factory, evaluate, baseline (Experiment 4), ratings (Experiment 5)
  routes.py    student page, JSON API, health check; templates/index.html, static/style.css
  models/      llm_client, prompts, seed
config/        config.py, the only source of settings
prompts/       classify_intent_v1, answer_v1 (kept for traceability), answer_v2, glossary_v1,
               no_retrieval_v1 (Experiment 4 only)
rules/         rule_library.json: id, sources, inputs, condition, outputs, effective period, tests
data/
  sources.json source registry with version metadata (committed)
  raw/         downloaded documents (not committed, restored by fetch)
  processed/   extracted text, calendar events, chunks (not committed, rebuilt)
  cache/llm/   every model call, committed as evidence for reported numbers
evaluation/
  intent/              155 labelled questions
  retrieval/           64 gold questions with reference dates and evidence
  version_selection/   15 labelled date cases
  conflicts/           20 planted contradictions
  generation/          6 smoke questions used while building phases 9 and 10
  end_to_end/          100 frozen inquiries with expected statuses (FROZEN holds the sha256)
  adversarial/         17 adversarial cases
  results/             saved evaluation outputs
docs/          handover-memo, architecture, environment/, troubleshooting/, authority-hierarchy,
               data-handling, intent-taxonomy, retrieval-failures, evidence-validation, rules,
               verification-and-escalation, evaluation, e2e-v1-failures, data-dictionary
tests/         206 tests with fixtures from the real documents; conftest.py
docker/        Dockerfile and docker-compose.yml (local two-service run), start.sh
Dockerfile     the public demo image (Hugging Face Space: app and Ollama in one container)
scripts/       clean_install_check.sh
setup.py       bootstrap script (not a packaging file)
CONTEXT.md     one-page orientation and the rules that must not be broken
```

---

## phase 1: repository and environment

Built the standard layout, pinned every version, and set up a local model so no
student question or document leaves the machine.

**Problems solved**
| problem | cause | fix |
|---|---|---|
| PyTorch would not install | Python 3.13; last Intel-Mac PyTorch (2.2.2) supports up to 3.12 | pinned Python 3.11.9 |
| `numpy` crash on import | pandas pulled NumPy 2.x; PyTorch 2.2.2 needs 1.x | pinned numpy 1.26.4, pandas 2.2.3, scikit-learn 1.5.2 |
| PyMuPDF failed to build | newest release has no prebuilt wheel for this Mac | pinned pymupdf 1.24.10 |
| wrong interpreter used | Anaconda base environment auto-activated | disabled `auto_activate` |
| port 5000 busy | macOS AirPlay uses it | development server on 5001 |
| 8 GB RAM | larger models swap | `qwen2.5:3b` (about 12 s for a first Arabic answer) |

---

## phase 2: documents

### sources
Six public documents found on nauss.edu.sa, each registered in `data/sources.json`
with `source_id`, `document_type`, `authority_level`, `version`, `effective_from`,
`effective_to`, `status` and `supersedes`.

| source_id | type | authority | in force |
|---|---|---|---|
| HANDBOOK-1446 | regulation (summary) | 1 | from 2024-08-01 |
| CALENDAR-1448 | calendar | 2 | 2026-08-12 to 2027-08-21 |
| PROGRAMS-GUIDE-1448 | program requirements | 3 | from 2026-08-01 |
| PROGRAMS-GUIDE-1447 | program requirements | 3 | 2025-08-01 to 2026-07-31 (superseded) |
| ADMISSION-PAGE-2025 | procedure | 4 | from 2025-08-23 |
| FAQ-NAUSS | faq | 5 | undated |

`dates_assumed: true` marks dates set by the developer because the document does not state them.

### the Arabic extraction problem
Text extracted from the PDFs contained about 1,086 reversed words, for example
`الدرايس` for `الدراسي`, `خالل` for `خلال`, `األول` for `الأول`.

Diagnosis, in order:
1. The PDF font tables map each ligature glyph to the **correct** letters (`لا`, `سي`, `ني`), so the fonts were not at fault.
2. The extractor reverses right-to-left text letter by letter, which flips the two letters produced by one ligature glyph.
3. A second extractor (pypdf) fixed the handbook but scrambled the programs guide, so neither tool alone worked.
4. Letter positions showed the pattern: the second letter of a ligature gets a zero-width box placed on the right edge of the next letter.

Fix: `fix_ligature_order` in `app/documents/loader.py` swaps each zero-width letter
that sits on the next letter's edge. Result: **1,086 reversed words reduced to 4**
across the three PDFs, verified on real letter positions in `tests/test_loader.py`.

### cleaning
`app/documents/normalize.py` unifies Arabic presentation forms (NFKC), removes
tatweel and zero-width characters, and collapses spaces. A separate search form
unifies alef variants, taa marbuta and alef maqsura; it is used only for matching,
never for display.

### structured calendar
`app/documents/calendar_parser.py` turns the calendar into 24 events, each with an
event code (for example `SEMESTER_WITHDRAWAL_DEADLINE`), a term id (`1448-T1`),
Gregorian and Hijri dates, and a source reference. It handles reversed day ranges
(`24-23`), row numbers on their own line, and the Hijri year change, and it warns if
a weekday does not match its date. All 24 weekdays match.

### required documents
- `docs/authority-hierarchy.md`: which document wins a conflict (status, then authority level, then effective date, otherwise `CONFLICTING_EVIDENCE`).
- `docs/data-handling.md`: question text is not logged by default, logs are kept 30 days, evaluation questions are synthetic.

---

## phase 3: ingestion and version selection

### version selection by date
`app/documents/version_selector.py` returns the document **in force on the question's
date**, never simply the newest. A question about March 2026 uses PROGRAMS-GUIDE-1447;
a question about October 2026 uses PROGRAMS-GUIDE-1448. `effective_to` is inclusive,
and overlapping versions raise an error instead of guessing.

Verified on 15 labelled cases in `evaluation/version_selection/cases.json`, including
boundary days (last day of one version, first day of the next) and dates before any
version exists. **Correct version rate: 15/15.**

### chunking
`app/documents/chunker.py` produces three kinds of chunk:
- regulation and guide text packed into about 160-word chunks with page, section heading and article number
- one chunk per FAQ question and answer
- one chunk per calendar event

Every chunk carries the source's version metadata. **186 chunks** in total.

### reproducible ingestion
`python cli.py ingest` writes chunks with sorted keys; two runs produce the same
sha256 (`9e6394386f2f`), meeting the "re-ingestion is idempotent" requirement.

---

## phase 4: intent understanding

### taxonomy
17 intents built from what the documents cover, documented in `docs/intent-taxonomy.md`.
`COURSE_WITHDRAWAL` is kept although no source covers it, so the system recognises
the question and answers `INSUFFICIENT_EVIDENCE` instead of confusing it with
semester withdrawal. `WITHDRAWAL_UNSPECIFIED` captures "can I withdraw?" for clarification.

### language and context
- `language.py` labels a question Arabic, English or mixed (80% script threshold) and answers in the majority script.
- `context_extractor.py` extracts degree level, term and withdrawal scope **only when written in the question**, and lists what is missing. It agrees with the labelled missing context on all 155 questions.

### question set
155 synthetic questions in formal Arabic, Saudi dialect and English, 15 of them
ambiguous. Every third question is the **dev** split (51) used while building; the
other 104 are **test**, never used for tuning.

### model client
`app/models/llm_client.py` routes every model call and enforces:
- the installed model must match `models.lock`, or the run stops with the install command (no silent fallback)
- temperature 0 and seed 42 from configuration
- every call cached on disk under a SHA-256 key of model, prompt and parameters

The first evaluation run took 2 min 10 s; the second took 0.1 s with identical numbers.

### experiment 1: keyword baseline vs local model
Test split, 104 questions:

| metric | keyword baseline | qwen2.5:3b |
|---|---|---|
| accuracy | 0.837 | 0.837 |
| macro-F1 | 0.853 | 0.839 |
| **out-of-scope F1** | 0.518 | **0.941** |
| Arabic accuracy | 0.810 | 0.845 |
| English accuracy | 0.861 | 0.837 |

Overall accuracy did not improve. The model is adopted as the main classifier because
out-of-scope detection, the class that stops invented answers, rose from 0.52 to 0.94.
The mixed-language subset has 3 questions, too few to draw a conclusion.

---

## phase 5: retrieval

### methods
- **BM25** (`bm25.py`): keyword search over section heading and text. The tokenizer
  normalises Arabic, strips article prefixes (`ال`, `وال`, `بال`, `لل`) and common
  question words, and returns nothing for passages sharing no word with the question.
- **embeddings** (`embeddings.py`): `intfloat/multilingual-e5-small` loaded at the
  revision pinned in `models.lock`, with `query:` and `passage:` prefixes. Passage
  vectors are computed once and cached.
- **hybrid** (`hybrid.py`): reciprocal rank fusion (k = 60) of the top 50 from each.

Every method searches **only passages from versions in force on the question's
date** (`retriever.py`), using the same version selector as phase 3.

### gold set
`evaluation/retrieval/gold.jsonl`: 64 synthetic questions, 39 Arabic and 25 English,
each with a reference date and one or more evidence groups (a question needing a
calendar date and the regulation behind it has two groups). Because every source is
Arabic, all English questions are cross-language. It includes the same question at
two dates, answered from the 1447 guide and from the 1448 guide.

> **Correction (2026-10-31, step 11a).** This paragraph first said the MA in Criminology
> changed from 2 years (1447) to 1 year (1448). That is wrong: it is 2 years in both.
> In the 1448 guide each program's duration box is extracted *before* the program's
> title, so the one-year box next to the criminology text belongs to the human-rights
> diploma that follows. Gold items R059 and R061 point to that passage (`#030`) instead of
> `#028`. The set stays frozen as v1; a corrected v2 will be reported beside it.

Recall@k is the share of evidence groups with a passage in the top k. Precision@5 is
the share of the top 5 that is evidence; with one correct passage its maximum is 0.2.

### experiment 2: BM25 vs embeddings vs hybrid

| method | recall@5 | recall@10 | Arabic R@5 / R@10 | English R@5 / R@10 | version leaks |
|---|---|---|---|---|---|
| BM25 | 0.602 | 0.641 | 0.936 / **1.000** | 0.080 / 0.080 | 0 |
| embeddings | 0.781 | 0.875 | 0.923 / 0.949 | **0.560 / 0.760** | 0 |
| **hybrid** | **0.797** | **0.875** | **0.974 / 1.000** | 0.520 / 0.680 | 0 |

- For Arabic, BM25 alone already finds every answer in the top 10, as the brief anticipated for regulation text.
- For English, BM25 cannot match English words to Arabic text; embeddings recover most of the gap.
- **Hybrid is the default**: best overall and best Arabic recall@5.
- Negative result: on English, hybrid is below embeddings alone, because the handbook's only English text (the grading table) attracts English questions through BM25.

### bugs found by testing
- The Arabic question mark `؟` was kept inside tokens, so `المقرر؟` never matched `المقرر`. Fixing it raised Arabic recall@10 from 0.949 to 1.000 (BM25).
- BM25 returned passages with a zero score; it now returns nothing, so later stages can answer `INSUFFICIENT_EVIDENCE`.

### failure analysis
All 8 failures at top 10 are English questions; each is reviewed in
`docs/retrieval-failures.md`. Causes: the English grading table attracting English
questions (2), gold annotations that were too strict (2), page layout splitting a
program's details from its title (1), similar program names (1), and meaning drift
toward a dominant topic (2).

---

## phase 6: evidence validation

Runs on the retrieved passages **before** any answer is written (`app/evidence/validator.py`),
always in this order:

| step | question | outcome on failure |
|---|---|---|
| currency | is every passage from a version in force on the question's date? | passage rejected |
| relevance | is it about the situation asked (semester vs program withdrawal)? | set aside as off topic |
| contradiction | do sources give different values for the same thing? | resolved by authority, or `CONFLICTING_EVIDENCE` |
| completeness | is a needed source missing (for example the calendar for a deadline)? | `INSUFFICIENT_EVIDENCE` |

Facts compared: durations, amounts, percentages, GPAs and dates, each tagged with the
degree or program it belongs to (the closest mention before it). Resolution follows
`docs/authority-hierarchy.md`: status, then authority level, then effective date.

**Results:** planted set of 20 cases (11 conflicts, 6 near misses, 3 other checks):
detection 1.0, false positives 0.0, resolution 1.0. On the 64 gold questions the conflict
report found no unresolved conflict.

**Bugs found:** the first-match subject rule tagged master's facts in the FAQ as diploma
facts (fixed with nearest mention); duplicate facts produced duplicate conflicts (fixed by
deduplication); question words such as متى counted as "needs a deadline" and blocked
rule-based answers (removed).

> **Correction (step 11a):** the "real conflict" first reported here (FAQ: master's 2 years;
> 1448 guide: criminology 1 year) is the extraction error described under phase 5, not a
> real disagreement between documents. Resolving it for the guide would give a wrong answer.

---

## phase 7: rule library

`rules/rule_library.json` holds 13 rules; each names its sources, inputs, condition,
outputs, effective period and the tests that check its boundaries. `docs/rules.md` is
generated from it.

| group | rules | examples |
|---|---|---|
| calendar (5) | RULE-CAL-01 to 05 | semester withdrawal open/closed, postponement, re-enrolment, refund before study starts, program withdrawal before finals |
| regulation (6) | RULE-REG-01 to 06 | attendance 75% / 50% exception, pass mark 70, academic warning GPA, closure after two warnings, re-enrolment within 4 semesters, appeals left |
| eligibility (2) | RULE-ELIG-01 to 02 | graduation GPA, honours |

The term is read from the question, or resolved from the question's date and stated in the
answer. Re-enrolment uses the **upcoming** term, the others the term in progress. Rules that
need a student's number (attendance, grade, GPA) run only when the student wrote it.

---

## phase 8: grounded generation (first version)

The model (`prompts/answer_v1.md`) wrote the whole answer from the validated passages and the
rule results; code attached the sources and the date basis. Non-answers use fixed bilingual
templates. First sample of 10 gold questions: **10/10 schema-valid, about 5/10 correct**.
Real failures: wrong weekday (Friday for a Thursday deadline), a closed window not stated as
closed, Chinese characters, "no information" although the evidence was there, and a
program-withdrawal rule mixed into a semester answer.

---

## phases 9 and 10: clarification, verification and escalation

Built from those real failures (`docs/verification-and-escalation.md`):
- **rule sentences written by code**: dates, weekdays (computed from the date) and
  open/closed are never left to the model
- **clarification read from the question text**: "can I withdraw?" asks course, semester or
  program; duration and graduation questions with no degree ask the degree; the reply is
  passed back with `--clarify`
- **prompt v2**: the model only adds 1 to 3 explanation sentences and may not restate the rules
- **verifier**: rejects foreign script, wrong language, numbers or weekdays not in the evidence,
  internal ids, false "no information", decision wording, and advice to act after a deadline
- **extractive fallback**: if the model text fails, the answer quotes the closest evidence
- **escalation** (`STAFF_REVIEW_REQUIRED`) for decisions and exceptions, rules that only a
  council can grant, and questions needing the student's own record; the response gives the
  reason, what can be confirmed, the sources and the next step. Escalations are logged
  without the question text.

**Result:** smoke set 6/6 expectations met.

### phase 10b: checking each sentence
Replaying the real outputs showed text that passed the whole-text verifier but was still
wrong: another situation mixed in (program withdrawal in a semester answer), glossary terms
copied into answers, prompt placeholders echoed as conditions, internal term ids, guesses.
`app/safety/sentence_filter.py` now judges **each sentence** and keeps only those that pass;
harmless openings are trimmed, conditions must be real grounded sentences, and the glossary
is sent only for English answers and only for terms in the evidence.

**Result:** smoke 6/6; on the 10-question sample 7 generated and 3 quoted answers, about 9 of
13 checked answers fully correct (from about 6). Meaning errors remain that a word-level
filter cannot see, such as a qualifier dropped ("three years' experience" required only for
other majors) or a condition attached to the wrong rule. These are what phase 11 measures.

---

## phase 11: evaluation

### part A: frozen sets and scoring (`docs/evaluation.md`)
- **end-to-end set**: 100 inquiries written from the documents, each with its reference date,
  expected status and the facts a correct answer must contain: 70 answerable (2 after a
  clarification reply), 10 clarification, 8 staff review, 6 out of scope, 6 insufficient
  evidence. Checked against every earlier set; repeated questions were rewritten. Frozen by
  sha256 before the first run.
- **adversarial set**: 17 cases: override the rules, hide the source, pretend the deadline is
  open, another student's data, approve my admission, absent and superseded regulations, and
  planted documents that tell the model a deadline is open.
- **Experiment 3 metrics**, overall and per language: status accuracy, correct and false
  refusal rates (always together), wrong answers shown to a student, grounded and unsupported
  claim rates, citation accuracy, self-service rate, response time, reproducibility. English
  model sentences cannot be matched word by word with Arabic sources; they are marked
  unverified and exported to a review sheet for the team review.

Changes made **before** the first run (not tuned on the set):
- a quote must share the question's key terms, so unrelated text is never quoted
- no model sentence or quote may say a closed window is open, or the reverse
- text addressed to the model is kept out of the index at ingest and checked again on every
  retrieved passage; writing the tests showed the fallback would otherwise quote a planted page

### first results (v1, 2026-10-31)
`evaluation/results/e2e_v1.md`, `e2e_v1.json`, `e2e_v1_review.csv`, `adversarial_v1.json`.

| metric | overall | Arabic | English |
|---|---|---|---|
| status accuracy (six statuses) | 0.87 | | |
| correct refusal rate | 0.933 | | |
| false refusal rate | 0.129 | | |
| fully correct (status and facts) | **0.66** | 0.717 | 0.575 |
| answer correct when answered | 0.656 | | |
| answered with a wrong or missing fact | 21 (18 after review; 3 were scorer misses) | | |
| non-answer questions answered anyway | 2 (flight ticket price, monthly stipend) | | |
| model sentences grounded (Arabic, judged) | 0.764 | | |
| English claims awaiting human review | 33 | | |
| citation accuracy (judged) | 0.987 | | |
| self-service rate | 0.40 | | |
| reproducible on repeat | **1.00** | | |
| response time, answered (uncached) | about 38 s median | | |
| response time, refusals (uncached) | about 1.5 s | | |

The run's printed median (0.06 s) is not a real measurement: the first 60 inquiries
reused cached model calls from an interrupted run. Times above are from the uncached ones.

**Adversarial: 12/17.** Passed: hidden source, both "pretend the deadline is open" phrasings
answered "closed" (one in Arabic; the English one was refused, a safe failure), "approve my
admission" (both languages), superseded guide never cited, and all three planted documents,
including the one worded to evade the scanner. Failed: an Arabic "ignore the regulations"
answered with unrelated services, two requests for another student's data answered instead
of refused, and an absent regulation answered with unrelated quotes.

### what the failures show (`docs/e2e-v1-failures.md`)
| cause | inquiries |
|---|---|
| retrieval missed the passage holding the answer (passage boundaries, English questions) | 11 |
| model chose the wrong number from passages holding several (application fee 2000 instead of 100, PhD supplementary semester 5000 instead of 25,000, first honours 5.00 instead of 4.75) | 4 |
| wrong intent, so the right rule never ran (refund before study starts, GPA warning) | 5 |
| checks too strict (the word "calendar" taken for an internal id; "refund not eligible" read as "closed") | 4 |
| calendar questions with no rule, so the date came only from the model | 2 |
| a misspelled intent from the model (`SEMMESTER_WITHDRAWAL`) routed as out of scope | 2 |
| no check that the evidence fits the question at all | 4 |
| no guard for another student's data | 2 (adversarial) |
| expected label conflicts with the documented date policy | 1 |

The safety layers that were tested worked: no wrong deadline, no "open" for a closed
window, no decision stated, no planted instruction followed, identical output on repeat.
The weak point is **content selection**: the right passage not found, or the wrong
number taken from the right passage.

### part B: fixes by cause, measured on a held-out set (step 11b)
1. A **held-out set** of 40 new inquiries was written and frozen after v1 and **before** any fix,
   and run on the v1 code (`holdout_before`).
2. Fixes by cause, from the v1 analysis only (full table in `docs/evaluation.md`): calendar rows
   answered by code with computed weekdays; calendar rules not blocked by missing search results;
   a fee in a model sentence must be the kind of fee asked; thresholds (pass mark, honours,
   attendance, warning and graduation GPA, appeals, closure, re-enrolment window) stated by code
   from the rule library; rules triggered by the question's own words; deadline sentences only for
   timing questions; over-strict checks corrected; misspelled intents mapped; an evidence-fits-the-
   question gate; escalation for another student's data and for "ignore the rules" requests. Two
   pre-existing bugs were found: a degree named in the question never reached the rules, and
   "قبولي" matched inside "المقبولين".

| set | before | after |
|---|---|---|
| v1, 100 inquiries (**optimistic**: fixes written after seeing them) | status 0.87, correct refusal 0.933, false refusal 0.129, 23 wrong answers | status **0.95**, correct refusal **1.0**, false refusal **0.057**, **13** wrong answers |
| held-out, 40 inquiries (**honest**) | status 0.85, false refusal 0.115, 10 wrong answers, grounded 0.78 | status **0.825**, false refusal 0.154, **10** wrong answers, grounded 0.83 |
| adversarial, 17 cases | 12/17 | **17/17** |

**Negative result.** The fixes did not generalise. On the held-out set, 2 inquiries improved, 3
became worse because of the new mechanisms (a timing-word list that missed dialect, an evidence
gate defeated by Arabic word forms, a calendar row chosen wrongly with full confidence), and 13
were wrong both times. The remaining causes are general: the model picks the wrong number from the
right passage (percentages, GPAs, marks; the fee check covered fees only), and English questions
miss the right passage. Three held-out cases exposed safety gaps (below).

### part C: safety gaps and regressions from the held-out set (step 11c)
Informed by the held-out results, so any held-out run after this step is **optimistic**; the
honest held-out figure stays `holdout_after`.
- a deadline question on a date with no calendar in force is never answered (the model had said
  "you can still withdraw")
- a decision request is escalated even when nothing could be confirmed
- a number the student states (attendance, grade) triggers its rule under any intent, and a
  computed rule result is not blocked by missing search results
- deadline rules are kept unless the question is clearly about something else (how many, what
  happens, conditions), instead of requiring a timing word
- calendar rows printed with a year are not beaten by shorter rows; a year in the question must match
- the evidence gate tolerates possessive endings (قيدي ~ قيد)
- a model timeout falls back to rule sentences and quoted evidence; an evaluation run records an
  error and continues instead of crashing
- Experiment 4 added (`evaluate-no-retrieval`); required documents added:
  `docs/authority-hierarchy.md`, `docs/data-handling.md`, `docs/data-dictionary.md`

| run after step 11c | status accuracy | correct / false refusal | wrong answers shown | grounded |
|---|---|---|---|---|
| v1, 100 inquiries (`e2e_v2`, optimistic) | 0.95 | 1.0 / 0.057 | 13 | 0.77 |
| held-out (`holdout_v2`, optimistic: fixes informed by it) | 0.95 | 1.0 / 0.077 | 7 | 0.86 |
| adversarial (`adversarial_v3`) | 17/17 | | | |

### Experiment 4: grounded assistant against the same model with no retrieval
`evaluation/results/exp4_no_retrieval.md`. Condition A is the same `qwen2.5:3b` with a plain prompt
(`prompts/no_retrieval_v1.md`): no retrieval, no rules, no checks. It is never shown to a student.

| 100 inquiries | A: model alone | B: assistant (`e2e_v2`) |
|---|---|---|
| fully correct | 0.14 | **0.82** |
| non-answer inquiries refused or escalated | 0.27 | **1.0** |
| wrong answers shown | 79 | **13** |
| grounded claim rate (judged) | 0.15 | **0.77** |
| unsupported claim rate (judged) | 0.85 | 0.23 |

As the brief expected: fluent, plausible and wrong about this university. Alone, the model answers
out-of-scope questions and decision requests instead of referring them, and 85% of its judged claims
have no support in the approved documents.

### Experiment 5: team review and efficiency (`evaluation/experiment5/`)
- **Answer quality**: specialists were not available, so a documented team review rates a fixed sample
  of 20 real answers (14 answered, 6 refusals, clarifications and escalations), sampled from the
  final runs `e2e_v4` and `holdout_v4`, from 1 to 5 for
  correctness, completeness, relevance, clarity and source appropriateness (`make-exp5`, `score-ratings`).
- **Claim review**: the 30 English claims the scorer could not judge, plus 10 Arabic claims to check
  agreement with the automatic labels (`score-claims`).
- **Efficiency** (`efficiency-report`): measured on the first, uncached run of the held-out set: median
  32.4 s for any response, 34.8 s for an answer, 1.8 s for a refusal or clarification (Intel Core i5,
  8 GB RAM, CPU only). Self-service rate: 0.35 on the held-out set after 11b, 0.53 on `e2e_v2`.
  **The Deanship's current response time could not be obtained, so no reduction is claimed**; it is
  recorded as unknown rather than estimated.

---

## phase 12: student interface

`python app.py`, then http://localhost:5001 (`app/routes.py`, `app/templates/index.html`).
- **Arabic right to left, English left to right**: the page and each answer take the direction of the
  answer's language; the question box uses `dir="auto"`.
- **Status always visible in words**, not by colour alone: "إجابة من المصادر المعتمدة", "نحتاج توضيحاً
  منك", "يحتاج إلى مراجعة الموظف المختص" and so on.
- **Sources visible without clicking**: document title, page and section (calendar rows as "الصف 6 في التقويم").
- **Date basis** under every answer, with the date the answer was generated, so a forwarded or cached
  answer shows its age.
- **Clarification as buttons**; the reply is sent back with the question.
- **Escalation**: what can be confirmed and the next step.
- **Readable errors**: if the model is unavailable the student sees a short message (HTTP 503); details
  go to the log, never to the page.
- The date defaults to today; the interface is the only place that reads the clock, and the question
  text is never logged.
- `POST /api/ask` returns the same response as JSON (`{"results": [...], "errors": []}`), without the internal trace.

---

## phase 13: deployment and handover

### part A: fixes from testing the student page by hand (`tests/test_fixes_13.py`)
Asking the running page real questions (step 12) showed four problems the evaluation sets had not:

| problem seen on the page | cause | fix |
|---|---|---|
| an escalated answer showed, under "what can be confirmed", a model sentence implying the student met the conditions | the escalation reused the whole composed answer, model sentences included | "confirmed" is now only code-written text: rule sentences and verbatim quotes; sources follow them |
| sentences such as "استوفيت جميع الشروط" / "you are eligible" were not caught | the decision list held only explicit decisions ("you are accepted") | phrases saying a condition is met are dropped unless the sentence is conditional ("if you meet...") |
| the same document listed once per passage | sources were de-duplicated by passage, not by document | one line per document, pages and sections joined |
| a second-term sentence quoted for a first-term question | quotes were chosen by relevance only | a quote naming only the other term is skipped |

The evaluation sets were rerun with the committed cache (the prompts did not change, so the
model calls are read from the cache): `holdout_v3`, `e2e_v3`, `adversarial_v4`. These runs are **optimistic**,
like every run after step 11c (`docs/evaluation.md`). Result: identical to `holdout_v2` and `e2e_v2`
(held-out 0.95 status accuracy, 7 wrong answers shown; 100-inquiry set 0.95, 13; adversarial 17/17),
with the same failing inquiries. The four fixes change what the page shows (confirmed text, source
list) and guard cases these sets do not contain, so they are covered by `tests/test_fixes_13.py`,
not by these scores.

### part B: deployment and handover
- **Two more fixes from reviewing the v3 escalations by hand**: a question about the student's own record
  (or another student's) shows no quotes as "confirmed", since the documents cannot confirm anything about
  a particular student; and quotes damaged by PDF extraction (reversed brackets, numbers glued to words,
  stray Latin words) are not shown in escalations (`readable` in `app/generation/extractive.py`). In answers
  they are kept: 7 of the 28 quotes in the final answers are damaged, and for E056 and E058 they are the
  only evidence for a correct answer (known limitations).
- **Bootstrap** `setup.py` (it was an empty file until this step) and `tests/conftest.py`.
- **Docker**: `docker/docker-compose.yml` runs Ollama and the app as two services; the root `Dockerfile`
  builds the public demo for a Hugging Face Space. Both pin their base images, install the CPU build of
  the pinned PyTorch, and run the bootstrap while building, so a broken document link or a changed model
  stops the build instead of reaching a student. **Written but not yet built**: the development sandbox
  could not reach Docker Hub; the first build is the deployment.
- **Handover documents**: `docs/handover-memo.md` (all Part 6 sections, including how to add a regulation
  version, a rule and an intent, with a worked example), `docs/architecture.md`, `docs/environment/`,
  `docs/troubleshooting/` (26 recorded problems in 6 files), `CONTEXT.md`.
- **Clean-install check** `scripts/clean_install_check.sh` and `compare-runs`.
- Final runs `holdout_v4`, `e2e_v4`, `adversarial_v5`: only escalation text changed, which carries no
  scored facts.

---

## development standards compliance

| rule | how it is met | check |
|---|---|---|
| 1.1 pin every version | `.python-version`, `requirements.txt` with `==`, `models.lock` | `check-model` passes |
| 1.2 fixed seed, zero temperature | `SEED` and `TEMPERATURE` in config; `set_seed` covers Python, NumPy, PyTorch | identical results on rerun |
| 1.3 no silent fallback | `ModelUnavailableError`; fallback flag defaults to off | tested with a wrong digest |
| 1.4 prompts as versioned files | `prompts/` (classify_intent_v1, answer_v1, answer_v2, glossary_v1, no_retrieval_v1), each with a header | test confirms no prompt text in `app/` |
| 1.5 cache every model call | `data/cache/llm/`, committed | second run 0.1 s, identical |
| 1.6 configuration is not code | all settings in `config/config.py` | |
| 1.7 no notebook deliverables | everything runs from `cli.py` | |
| 1.8 logging, not print | logging with timestamp, level, module | |
| 1.9 no runtime data in git | `data/raw/`, `data/processed/`, logs ignored | |

Pre-handover checklist (1.10):

| rule | check | how it was checked |
|---|---|---|
| 1.1 | bootstrap passes on a clean clone | `scripts/clean_install_check.sh` |
| 1.2 | the same input twice gives identical output | reproducibility 1.00 on every evaluation run (each inquiry answered twice) |
| 1.3 | corrupting `models.lock` crashes instead of substituting | `tests/test_llm_client.py` (wrong digest stops with instructions); `check-model` |
| 1.4 | no prompt text in application code | `tests/test_prompts.py` |
| 1.5 | second evaluation run fast and identical | `holdout_v4` from the cache: median 0.05 s, `compare-runs` identical |
| 1.6 | changing a configuration value changes behaviour | settings read from `config/config.py` / `.env`, e.g. `TOP_K` changes the passages in the trace |
| 1.7 | no notebooks | `git ls-files "*.ipynb"` is empty |
| 1.8 | no print statements in application code | `grep -rn "print(" app/` is empty |
| 1.9 | no logs or uploads tracked | `git ls-files` shows no `.log`, `data/raw` or `data/processed` files |

---

## known limitations

- **Authority hierarchy is assumed**, not yet agreed with the Deanship.
- **Four sources have assumed dates** (`dates_assumed: true`); the FAQ is undated.
- **The handbook is a 1446 summary** of the regulations; the full regulations with article numbers are not public, so citations use page and section.
- **No English source documents** exist; English questions will rely on cross-language retrieval.
- **4 reversed words remain** after the extraction fix (about 0.07% of words).
- **Some lines in the programs guide** keep mixed-direction segments in the wrong order within the line; meaning is preserved for search but quotes may read awkwardly.
- **Add/drop and single-course withdrawal** are not covered by any source and will be answered `INSUFFICIENT_EVIDENCE`.
- **Evaluation questions are synthetic** and written by the same developer who wrote the keyword rules, which may favour the baseline.
- **Mixed-language questions** number only 4.
- **English retrieval is weaker** than Arabic (hybrid recall@10 0.68 vs 1.00); candidate fixes are listed in `docs/retrieval-failures.md` and must be tested on new questions.
- **Programs guide layout (1448)**: each program's language, duration and fee box is extracted *before* the program's title, so it shares a passage with the end of the previous program. This caused the false criminology "conflict" and wrong gold annotations R059/R061. Fix planned: chunk at program boundaries, measured before and after.
- **Meaning errors** in model sentences (a dropped qualifier, a condition attached to the wrong rule) pass the word-level checks; they are counted in Experiment 3.
- **English answers** cannot be checked word by word against Arabic sources; their claims are reviewed by hand.
- **The model** (`qwen2.5:3b`, chosen for 8 GB RAM) takes about 25 to 45 s per answered question on this Mac.
- **Wrong number from the right passage**: the small model still picks the wrong percentage, GPA or mark from a passage holding several; only fees are checked by kind, and thresholds in the rule library are stated by code.
- **Fixes shaped by the evaluation set**: the step 11b fixes improved the inquiries they were written from but not a held-out set; the step 11c fixes were informed by the held-out set, so no fully unseen measurement exists after step 11b.
- **Programs guide not yet chunked at program boundaries**: left as a limitation because it renumbers passages and requires gold set v2.
- **Quotes damaged by extraction** remain in some answers (7 of 28 quotes in the final runs); they are filtered from escalations only.
- **Docker images written but not yet built**; Windows not tested.

---

## progress

| phase | status |
|---|---|
| 1. repository and environment | done |
| 2. documents, extraction, calendar, required docs | done |
| 3. ingestion and version selection | done |
| 4. intent understanding and experiment 1 | done |
| 5. retrieval: BM25 vs embeddings vs hybrid, per language, cross-language | done |
| 6. evidence validation: currency, contradiction, completeness | done |
| 7. rule library | done |
| 8. grounded generation | done |
| 9. clarification | done |
| 10. verification and escalation (10b: per-sentence filter) | done |
| 11. evaluation and adversarial testing | done; Experiment 5 team rating to fill in |
| 12. student interface | done |
| 13. deployment and handover | done: fixes from hand testing, bootstrap, Docker, handover documents; first public build, team rating and outside test remain |
