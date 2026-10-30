# admission-registration-assistant

An assistant for the Admission and Registration department of Naif Arab University
for Security Sciences (NAUSS). It answers student questions in Arabic and English
**only from approved institutional documents**, cites the document and section it
used, and refers the student to staff when the evidence is missing, contradictory,
or the question needs an official decision.

Project 5A, Data Science course. Built to the project brief and the Development
Standards document.

> **Status:** phases 1 to 5 of 13 complete. The system can load, clean, version and
> chunk the documents, classify questions, and retrieve the right passages for the
> question's date. Evidence validation and answering come next.

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
| automated tests | 78 passing |
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

**4. create the environment file**
```bash
cp .env.example .env
```
Check: `cat .env` shows `LLM_MODEL=qwen2.5:3b`.

**5. install and verify the local model**
```bash
ollama pull qwen2.5:3b
python cli.py check-model
```
Check: `OK: qwen2.5:3b matches models.lock (357c53fb659c)`.

**6. download the source documents**
```bash
python cli.py fetch
```
Check: `ls data/raw` lists 6 files.

**7. build the calendar and the chunks**
```bash
python cli.py build-calendar
python cli.py ingest
```
Check: `CALENDAR-1448: 24 events` and `186 chunks ... (sha256 9e6394386f2f)`.

**8. run the tests**
```bash
python -m pytest
```
Check: `78 passed`.

**9. run retrieval once** (downloads the pinned embedding model, about 470 MB, on first use)
```bash
python cli.py evaluate-retrieval --method all
```
Check: three methods reported, each with `version leaks=0`.

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
  documents/   loader, normalize, calendar_parser, chunker, version_selector, registry, ingest
  intent/      taxonomy, language, keyword_baseline, llm_classifier, context_extractor, evaluate
  retrieval/   tokenize, bm25, embeddings, hybrid, retriever, evaluate, factory
  models/      llm_client, prompts, seed
config/        config.py, the only source of settings
prompts/       versioned prompt files (classify_intent_v1.md)
data/
  sources.json source registry with version metadata (committed)
  raw/         downloaded documents (not committed, restored by fetch)
  processed/   extracted text, calendar events, chunks (not committed, rebuilt)
  cache/llm/   every model call, committed as evidence for reported numbers
evaluation/
  intent/              155 labelled questions
  retrieval/           64 gold questions with reference dates and evidence
  version_selection/   15 labelled date cases
  results/             saved evaluation outputs
docs/          authority-hierarchy.md, data-handling.md, intent-taxonomy.md, retrieval-failures.md
tests/         78 tests with fixtures from the real documents
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
two dates where the guide changed: the MA in Criminology is 2 years in the 1447 guide
and 1 year in the 1448 guide.

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

## development standards compliance

| rule | how it is met | check |
|---|---|---|
| 1.1 pin every version | `.python-version`, `requirements.txt` with `==`, `models.lock` | `check-model` passes |
| 1.2 fixed seed, zero temperature | `SEED` and `TEMPERATURE` in config; `set_seed` covers Python, NumPy, PyTorch | identical results on rerun |
| 1.3 no silent fallback | `ModelUnavailableError`; fallback flag defaults to off | tested with a wrong digest |
| 1.4 prompts as versioned files | `prompts/classify_intent_v1.md` with header | test confirms no prompt text in `app/` |
| 1.5 cache every model call | `data/cache/llm/`, committed | second run 0.1 s, identical |
| 1.6 configuration is not code | all settings in `config/config.py` | |
| 1.7 no notebook deliverables | everything runs from `cli.py` | |
| 1.8 logging, not print | logging with timestamp, level, module | |
| 1.9 no runtime data in git | `data/raw/`, `data/processed/`, logs ignored | |

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
- **Programs guide layout**: each program's language, duration and fee box lands in the same passage as the start of the next program.

---

## progress

| phase | status |
|---|---|
| 1. repository and environment | done |
| 2. documents, extraction, calendar, required docs | done |
| 3. ingestion and version selection | done |
| 4. intent understanding and experiment 1 | done |
| 5. retrieval: BM25 vs embeddings vs hybrid, per language, cross-language | done |
| 6. evidence validation: currency, contradiction, completeness | next |
| 7. rule library | |
| 8. grounded generation | |
| 9. clarification | |
| 10. verification and escalation | |
| 11. evaluation and adversarial testing | |
| 12. student interface | |
| 13. deployment and handover | |
