# handover memo

For the maintainer who takes over this system and has never met its author. Written to Part 6 of
the Development Standards and Phase 8 of the project brief. Read `README.md` first for installation;
this memo covers what the README does not: what is finished, why it is built this way, how to
debug it, what will break, and how to extend it.

Last updated: 2026-10-31 (step 13c).

---

## 1. what was built

An assistant for the Deanship of Admission and Registration at NAUSS. A student asks in Arabic or
English; the system answers **only from the six approved public documents**, cites the document and
section, states the date the answer applies to, and refers the student to staff when the evidence is
missing or contradictory or the question needs a decision. It runs entirely on one computer: a local
model through Ollama and a local embedding model; no question leaves the machine.

| component | state | acceptance evidence |
|---|---|---|
| document registry, extraction, version selection by date | complete | 15/15 labelled date cases; re-ingestion byte-identical (sha256 `9e6394386f2f`); new version added with `add-source`, no code change |
| structured academic calendar | complete | 24 events, each weekday checked against its date |
| intent classification (17 labels) | complete, with a known weakness | Experiment 1: accuracy 0.837, out-of-scope F1 0.941 |
| retrieval (BM25, embeddings, hybrid) | complete for Arabic; **weak for English** | Experiment 2: Arabic recall@10 1.00, English 0.68; 0 passages from versions not in force |
| evidence validation (currency, relevance, contradiction, completeness) | complete | 20 planted conflicts: detection 1.0, false positives 0.0 |
| rule library (13 rules) | complete | boundary tests for every rule (`tests/test_rules.py`) |
| answer composition and checks | complete; see limitations | Experiment 3 (below) |
| clarification and escalation | complete | 17/17 adversarial cases |
| student page and JSON API | complete | `tests/test_app.py`; tested by hand in Arabic and English (step 12) |
| bootstrap (`setup.py`) and clean-install check | complete | `scripts/clean_install_check.sh` passed on a fresh clone: 211 tests, held-out results reproduced 40 of 40 |
| public demo (Hugging Face Space, root `Dockerfile`) | complete | built and running at https://huggingface.co/spaces/m11ram/admission-registration-assistant; answered test questions correctly in Arabic |
| local two-service Docker run (`docker/docker-compose.yml`) | **written, not yet run** | same base images and bootstrap as the Space image |
| Experiment 5 team rating | **incomplete** | sheets generated from the final runs (`evaluation/experiment5/`), not yet filled |
| user evaluation, students and staff separately | **not done yet** | protocol, form and `score-feedback` ready (`evaluation/user_evaluation/`) |
| test with someone outside the team | **not done yet** | required by the brief and the standards; form in `evaluation/user_evaluation/README.md` |
| Windows | **untested** | developed and measured on macOS only |
| response time on the public demo | **not measured** | the start-up `speed on this machine` line and the `answered:` lines in the Space's container log give it |

Why the incomplete items are incomplete: they need people (reviewers, students, staff, an outsider) or a
Windows machine. None of them is blocked by code.

---

## 2. architecture and reasoning

The full design, the stage order and a table of every non-obvious decision with its reason are in
`docs/architecture.md`. The short version:

- **The code decides; the model only phrases.** Dates, weekdays, open/closed, thresholds, which version
  is in force, whether sources disagree and whether to answer at all are decided by tested code. The
  model labels the intent and adds up to three sentences, each checked; when it fails, verbatim quotes
  or an honest non-answer are used instead.
- **The order of stages matters.** The third-party guard comes first (never retrieve another student's
  data). Clarification comes before out-of-scope (a vague "I want to withdraw" was being refused).
  Evidence validation runs before any text is written (an answer is never written from a superseded or
  contradicted passage). Escalation comes last so the student still sees what can be confirmed.
- **`as_of` is an input.** Nothing below the interface reads the clock, so every result is reproducible
  and every answer states its date basis.

Parameter values and their reasons: retrieval `TOP_K=5`, `RETRIEVAL_CANDIDATES=50`, `RRF_K=60` (standard
RRF constant, not tuned); generation `GEN_EVIDENCE_LIMIT=3`, `GEN_EVIDENCE_CHARS=700` (short prompts for a
3B model on 8 GB); `TEMPERATURE=0`, `SEED=42` (reproducibility); `LLM_TIMEOUT=300` locally and 600 in the
Docker images (a slower CPU). All are in `config/config.py` and can be set in `.env`.

---

## 3. how to run it, step by step

`README.md` gives the installation (Python 3.11.9, pinned packages, Ollama, `python setup.py`). Here is
what each step produces and how to run one component alone.

| step | command | intermediate data | look at it with |
|---|---|---|---|
| download | `python cli.py fetch` | `data/raw/` 4 PDF + 2 HTML | file sizes in the log |
| inspect extraction | `python cli.py peek` | `data/processed/peek/<source>.txt` | any text editor (check Arabic word order) |
| calendar | `python cli.py build-calendar` | `data/processed/calendar/CALENDAR-1448.json`: row, event, code, term, Gregorian and Hijri dates, weekday | the JSON |
| chunks | `python cli.py ingest` | `data/processed/chunks.jsonl`: one passage per line with source metadata; `quarantine.json` | `head -1 data/processed/chunks.jsonl` |
| embeddings | first search or `python setup.py` | `data/processed/embeddings/passages_<hash>.npy` | — |
| model check | `python cli.py check-model` | — | prints the installed digest |

Running one component alone, for debugging:

```bash
python cli.py search "متى آخر موعد للاعتذار؟" --as-of 2026-10-14      # retrieval only: top passages for a date
python cli.py rule RULE-CAL-01 --as-of 2026-11-20 --term 1448-T1        # one rule on one date
python cli.py rule RULE-REG-01 --as-of 2026-10-14 --input attendance_percent=70
python cli.py ask "كم نسبة الحضور المطلوبة؟" --as-of 2026-10-14          # whole pipeline, prints the response and its trace
python cli.py evaluate-conflicts                                       # evidence validation on the planted set
python -m pytest tests/test_rules.py -q                                # one module's tests
```

The **trace** printed by `ask` (and stored in every evaluation row) shows each stage: intent, retrieved
chunk ids, quarantined ids, evidence status, rules and outputs, the gate, sentences kept and dropped with
the reason, the mode (`generated`, `extractive`, `templated`, `escalated`). Start every investigation
there: it says which stage made the decision.

The model cache (`data/cache/llm/`) means an evaluation question already asked is answered instantly and
identically. To see the real speed, point `CACHE_DIR` at an empty folder.

---

## 4. known bugs and limitations

Everything known to be wrong, untested or handled badly, most serious first.

1. **Wrong number from the right passage.** The 3B model sometimes takes the wrong percentage, GPA or mark
   from a passage that holds several. Fees are checked by kind and the main thresholds are written by code
   from the rule library, but other numbers are not. Most of the 7 (held-out) and 13 (100-inquiry) wrong
   answers in the final runs are this or the next item.
2. **English retrieval is weak** (recall@10 0.68 against 1.00 for Arabic): every source is Arabic, so English
   questions depend on cross-language embeddings. Candidate fixes are in `docs/retrieval-failures.md`; none was
   measured on new questions.
3. **Programs-guide layout (1448)**: each program's language, duration and fee box is extracted before the
   program's title, so it shares a passage with the previous program. Caused the false criminology conflict
   and wrong gold items R059/R061. Fix (chunk at program boundaries) renumbers passages and needs gold set v2;
   not done.
4. **Quotes damaged by extraction.** Some verbatim quotes show reversed brackets or numbers glued to words
   (for example "الفصل75%("). Since step 13c escalations show no quotes, and an answer with a rule sentence
   quotes only the calendar row the rule cites; an answer without a rule sentence can still show a damaged
   quote (one in the final runs, E042). Quotes chosen by relevance can also drift to a neighbouring topic of
   the same handbook page (seen on the public demo; why rule-backed answers no longer quote the handbook).
5. **Meaning errors pass the word-level checks**: a dropped qualifier, or a condition attached to the wrong
   rule. The checks compare words, numbers, weekdays and open/closed; they do not understand meaning.
6. **Fixes shaped by the evaluation sets.** The honest held-out figure is `holdout_after` (status accuracy
   0.825); every later held-out run is optimistic because later fixes were informed by it.
7. **Evaluation questions are synthetic**, written by the developer; no real inquiry log was available.
   Only 4 mixed-language questions.
8. **Authority order and four document dates are assumed** (`docs/authority-hierarchy.md`,
   `dates_assumed` in `data/sources.json`); the Deanship has not confirmed them. E008's expected label
   conflicts with the assumed calendar start date.
9. **The handbook is a 1446 summary**; the full regulations with article numbers are not public.
10. **Add/drop and single-course withdrawal** are not in any source: always `INSUFFICIENT_EVIDENCE`.
11. **Response time**: about 32 s median per question on the development Mac (CPU); not yet measured on the
    public demo's shared CPU, where a new question froze before step 13d (a 600 s timeout retried twice). Since
    then a model call waits at most 180 s there and is never retried after a timeout; the intent falls back to the
    keyword classifier and the answer to the rule sentence. The demo depends on a paid Hugging Face plan (Docker Spaces need PRO as of
    October 2026).
12. **Adding an intent touches several files** (section 6), more than the "small fixed number of edits" the
    standards ask for. Prompt versions are chosen by constructor defaults (`classify_intent_v1`, `answer_v2`)
    rather than by configuration.
13. **Untested**: Windows; the local two-service Docker run; the outside-user test and the user evaluation.

---

## 5. what breaks and how to fix it

| dependency | how you would notice | what to do |
|---|---|---|
| **university website** (`data/sources.json` URLs) | `fetch` logs "could not download"; `setup.py` stops with "documents not downloaded" | find the new URL on nauss.edu.sa, update `url` in `data/sources.json`, run `fetch` again |
| **document content changes** (same URL, new file) | `setup.py` warns that the chunk hash differs from `9e6394386f2f` | treat it as a new version: `add-source` with new `source_id`, version and dates (section 6), so old dates keep the old text; re-run the evaluations and report both |
| **new academic year** | deadline questions dated 2027-08-22 or later answer `INSUFFICIENT_EVIDENCE` (the 1448 calendar is in force until 2027-08-21) | add the new calendar with `add-source --type calendar` and `build-calendar`; check `calendar_parser.py` still reads every row (24 events this year) |
| **Ollama model tag** (`qwen2.5:3b` updated upstream) | `check-model` fails: installed digest differs from `models.lock` | do not just update the lock. Pull the old digest if available; otherwise update `models.lock`, re-run every evaluation, report old and new numbers (the committed cache no longer matches) |
| **Ollama not running / slow** | page shows "temporarily unavailable" (HTTP 503) or answers fall back to quotes; log says "model unavailable" | start the Ollama app; raise `LLM_TIMEOUT` on slow machines |
| **Ollama version** (Docker images pin `ollama/ollama:0.35.0`) | image build fails, or output differs from the cache | pin a tag that exists; outputs at temperature 0 can change across versions, so re-run evaluations after changing it |
| **embedding model** (Hugging Face repo) | `setup.py` step 4 fails; or the revision in `models.lock` is no longer downloadable | the revision is a commit hash, so the weights cannot change silently; if the repository disappears, choose a new model, update the lock and re-run Experiment 2 and the end-to-end sets |
| **PyTorch / Python** | `pip install` fails on Python 3.12+ on Intel Macs | use Python 3.11.9 (`.python-version`); see `docs/troubleshooting/python-and-packages.md` |
| **NumPy 2** | import errors in torch or scikit-learn | keep `numpy==1.26.4` |
| **PyMuPDF** | Arabic words reversed again, or `peek` text differs | keep `PyMuPDF==1.24.10`; the repair in `app/documents/loader.py` depends on how this version orders glyphs |
| **Hugging Face Spaces** | build log error, or the Space sleeps | rebuild from the Space settings; free Spaces sleep after inactivity and the first question after waking is slow |
| **Space hardware too slow** | container log: low `speed on this machine` at start-up, `model unavailable ... ReadTimeout`, answers without model sentences | choose larger hardware in the Space settings (paid), or raise `LLM_TIMEOUT` in the root `Dockerfile` and accept longer waits |
| **Docker Hub images** (`python:3.11.9-slim`, `ollama/ollama:0.35.0`) | build cannot pull an image | pin another existing tag of the same version line |

---

## 6. how to extend it

The three procedures the brief asks for, then one worked example.

### add a new regulation or document version (no code change)
```bash
python cli.py add-source --file ~/Downloads/handbook-1448.pdf \
  --source-id HANDBOOK-1448 --title "دليل الطالب 1448هـ" \
  --type regulation --authority 1 --version 1448 \
  --effective-from 2026-08-23 --supersedes HANDBOOK-1446 \
  --url https://nauss.edu.sa/...
python cli.py peek          # check the Arabic text reads correctly
python cli.py ingest        # (and build-calendar for a calendar)
python -m pytest -q
```
The superseded version is closed the day before the new one starts and kept, so questions about earlier
dates still use it. If a rule's threshold changed, add a new rule entry with `effective_from` (below).

### add a rule
1. add an entry to `rules/rule_library.json`: `rule_id`, `title`, `kind` (`calendar` or `regulation`),
   `inputs`, `outputs`, `condition`, `sources`, `effective_from`/`effective_to`, `tests`;
   a calendar rule names an `event_code` the calendar parser produces; a regulation rule names a `function`
2. for a regulation rule, write that function in `app/rules/registration_rules.py` (returns `(output, details)`)
3. map it to intents in `RULES_BY_INTENT` (and `TRIGGERS` if the question's words should trigger it) in
   `app/rules/selection.py`
4. write its sentence in `app/generation/rule_sentences.py` (`CALENDAR` or `THRESHOLDS`), both languages
5. boundary tests in `tests/test_rules.py`; run `python cli.py rules-doc` to regenerate `docs/rules.md`

### add an intent
1. `app/intent/taxonomy.py`: the label and its meaning (and `REQUIRED_CONTEXT` if it needs clarification)
2. a new prompt version `prompts/classify_intent_v2.md` with the label and examples (never edit v1: results
   were measured with it), and select it in `app/pipeline/factory.py`
3. `app/intent/keyword_baseline.py`: keywords, so the baseline stays comparable
4. `app/evidence/relevance.py` and `validator.py` (`FACT_TYPES`): what makes a passage relevant and which
   facts are compared; `completeness.py` if it needs the calendar
5. `app/rules/selection.py` if rules apply; `app/safety/sentence_filter.py` `OTHER_SITUATION` if it is easily
   confused with another intent
6. labelled questions in a **new** version of the intent set, re-run Experiment 1, update `docs/intent-taxonomy.md`

### worked example: the threshold for honours changes
Suppose the 1448 handbook raises first-class honours from 4.75 to 4.80 from 2026-08-23.
1. `add-source` the new handbook (above), superseding HANDBOOK-1446.
2. In `rules/rule_library.json`, set `"effective_to": "2026-08-22"` on `RULE-ELIG-02` and add `RULE-ELIG-02B` with
   the same fields, `"effective_from": "2026-08-23"`, sources pointing to HANDBOOK-1448, and a function
   `honours_1448` in `registration_rules.py` with the new threshold.
3. Add `RULE-ELIG-02B` wherever `RULE-ELIG-02` is listed in `selection.py`, and its statement in
   `rule_sentences.py` `STATEMENTS`.
4. Tests: a GPA of 4.78 on 2026-08-22 gives first class, on 2026-08-23 second class.
5. `python -m pytest -q`, `python cli.py rules-doc`, then re-run the end-to-end sets and report both versions.
Four edits plus a test and the generated doc: within the standards' extension test.

---

## 7. measured results and their conditions

**Conditions.** MacBook Pro, Intel Core i5, 8 GB RAM, CPU only, macOS 15; Python 3.11.9; packages as in
`requirements.txt`; `qwen2.5:3b` digest `357c53fb659c`; `intfloat/multilingual-e5-small` revision `614241f6`;
temperature 0, seed 42; chunks sha256 `9e6394386f2f`; frozen sets sha256 in `evaluation/end_to_end/FROZEN`
(100 inquiries `1d187245c016`, held-out 40 `3ee21c4c6cff`). All questions synthetic. Labels are automatic
first-pass labels; English claims need human review.

| experiment | result | file |
|---|---|---|
| 1. intent: keywords vs model (104 test questions) | accuracy 0.837 both; out-of-scope F1 0.518 → **0.941** | `evaluation/results/` (intent) |
| 2. retrieval (64 gold questions) | hybrid recall@10 0.875 (Arabic 1.00, English 0.68); 0 version leaks | `evaluation/results/` (retrieval) |
| evidence validation (20 planted) | detection 1.0, false positives 0.0, resolution 1.0 | `evaluate-conflicts` |
| 3. first end-to-end run (`e2e_v1`, 100) | status 0.87, 66/100 fully correct, 23 wrong answers | `e2e_v1.md` |
| 3. **held-out, honest** (`holdout_before` → `holdout_after`, 40) | status 0.85 → **0.825**; 10 wrong answers both times. **The step 11b fixes did not generalise** | `holdout_after.md` |
| 3. final runs (`e2e_v5`, 100, optimistic) | status 0.95; correct refusal 1.0; false refusal 0.057; 13 wrong answers; grounded 0.807; citation accuracy 0.978 | `e2e_v5.md` |
| 3. final runs (`holdout_v5`, 40, optimistic) | status 0.95; correct refusal 1.0; false refusal 0.077; 7 wrong answers; grounded 0.857; citation accuracy 1.0 | `holdout_v5.md` |
| adversarial (17) | 12/17 first run → **17/17** (every run since step 11b) | `adversarial_v6.json` |
| 4. model alone, no retrieval (100) | 14/100 correct and 79 wrong answers, against 82/100 and 13 for the assistant | `exp4_no_retrieval.md` |
| 5. efficiency (held-out, uncached) | median 32.4 s per response; 34.8 s answered; 1.8 s refusal or clarification; Deanship baseline **unknown** | `exp5_efficiency.md` |
| 5. team rating | not yet filled | `evaluation/experiment5/` |
| 5. user evaluation | not yet run | `evaluation/user_evaluation/` |
| reproducibility | 1.00 on every run (each inquiry answered twice) | every results file |

The step 13 runs (`*_v3` to `*_v5`) changed only what answers quote and what escalations show; statuses,
correctness and the number of wrong answers stayed the same throughout. `README.md` ("required metrics")
lists every metric the brief requires with its value and file.
