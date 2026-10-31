"""Run project tasks from the command line."""
import argparse
import hashlib
import json
import logging
import shutil
import time
from pathlib import Path

import requests

from config.config import config_by_name

log = logging.getLogger("cli")


def load_sources(cfg):
    """Read the sources file."""
    return json.loads(Path(cfg.SOURCES_FILE).read_text(encoding="utf-8"))


def fetch(cfg, args):
    """Download every source listed in the sources file into the raw folder."""
    raw = Path(cfg.RAW_DIR)
    raw.mkdir(parents=True, exist_ok=True)
    headers = {"User-Agent": "Mozilla/5.0 (admission-registration-assistant)"}
    for s in load_sources(cfg):
        target = raw / s["filename"]
        if target.exists():
            log.info("skip %s (already downloaded)", s["source_id"])
            continue
        if not s.get("url"):
            log.error("%s has no url and its file is missing: %s", s["source_id"], target)
            continue
        for attempt in range(3):
            try:
                r = requests.get(s["url"], headers=headers, timeout=30)
                r.raise_for_status()
                target.write_bytes(r.content)
                log.info("saved %s -> %s (%d KB)", s["source_id"], target, len(r.content) // 1024)
                break
            except requests.RequestException as e:
                wait = 2 ** attempt
                log.warning("%s failed (%s), retrying in %ss", s["source_id"], e, wait)
                time.sleep(wait)
        else:
            log.error("could not download %s from %s", s["source_id"], s["url"])


def peek(cfg, args):
    """Write the extracted text of every source to a file for inspection."""
    from app.documents.loader import extract_pages

    out_dir = Path(cfg.PROCESSED_DIR) / "peek"
    out_dir.mkdir(parents=True, exist_ok=True)
    for s in load_sources(cfg):
        pages = extract_pages(Path(cfg.RAW_DIR) / s["filename"])
        empty = sum(1 for p in pages if len(p.strip()) < 20)
        parts = [f"===== page {i} =====\n{p}" for i, p in enumerate(pages, 1)]
        (out_dir / f"{s['source_id']}.txt").write_text("\n".join(parts), encoding="utf-8")
        log.info("%s: %d pages, %d empty, %d chars",
                 s["source_id"], len(pages), empty, sum(len(p) for p in pages))


def build_calendar(cfg, args):
    """Parse every calendar source into structured events."""
    from app.documents.calendar_parser import parse_calendar
    from app.documents.loader import extract_pages

    out_dir = Path(cfg.PROCESSED_DIR) / "calendar"
    out_dir.mkdir(parents=True, exist_ok=True)
    for s in load_sources(cfg):
        if s["document_type"] != "calendar":
            continue
        text = "\n".join(extract_pages(Path(cfg.RAW_DIR) / s["filename"]))
        events = parse_calendar(text, s["source_id"], s["version"])
        target = out_dir / f"{s['source_id']}.json"
        target.write_text(json.dumps(events, ensure_ascii=False, indent=2), encoding="utf-8")
        log.info("%s: %d events -> %s", s["source_id"], len(events), target)


def ingest(cfg, args):
    """Chunk every source into one JSON-lines file; identical input gives identical output."""
    from app.documents.ingest import build_chunks
    from app.documents.injection import split_flagged

    chunks = []
    for s in load_sources(cfg):
        part = build_chunks(s, cfg.RAW_DIR)
        log.info("%s: %d chunks", s["source_id"], len(part))
        chunks.extend(part)
    chunks, flagged = split_flagged(chunks)
    quarantine = Path(cfg.PROCESSED_DIR) / "quarantine.json"
    quarantine.parent.mkdir(parents=True, exist_ok=True)
    quarantine.write_text(json.dumps(flagged, ensure_ascii=False, indent=2), encoding="utf-8")
    for f in flagged:
        log.warning("kept out of the index (text addressed to the model): %s %s", f["chunk_id"], f["signals"])
    out = Path(cfg.PROCESSED_DIR) / "chunks.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    body = "".join(json.dumps(c, ensure_ascii=False, sort_keys=True) + "\n" for c in chunks)
    out.write_text(body, encoding="utf-8")
    digest = hashlib.sha256(body.encode("utf-8")).hexdigest()[:12]
    log.info("%d chunks -> %s (sha256 %s)", len(chunks), out, digest)


def add_source_cmd(cfg, args):
    """Register a new document version and copy its file into the raw folder."""
    from app.documents.registry import add_source

    src_file = Path(args.file)
    if not src_file.exists():
        log.error("file not found: %s", src_file)
        return
    filename = f"{args.source_id}{src_file.suffix.lower()}"
    new = {
        "source_id": args.source_id, "title": args.title, "document_type": args.type,
        "authority_level": args.authority, "version": args.version,
        "effective_from": args.effective_from, "effective_to": args.effective_to,
        "language": args.language, "supersedes": args.supersedes,
        "url": args.url, "filename": filename,
    }
    sources = add_source(load_sources(cfg), new)
    raw = Path(cfg.RAW_DIR)
    raw.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src_file, raw / filename)
    Path(cfg.SOURCES_FILE).write_text(
        json.dumps(sources, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    log.info("added %s (supersedes %s); run 'python cli.py ingest' next",
             args.source_id, args.supersedes or "nothing")


def evaluate_intent(cfg, args):
    """Score an intent classifier on the labelled set and save the results."""
    from app.intent.evaluate import evaluate, load_questions

    split = None if args.split == "all" else args.split
    rows = load_questions(Path(cfg.EVAL_DIR) / "intent" / "questions.jsonl", split)
    if args.method == "keyword":
        from app.intent.keyword_baseline import classify
    else:
        from app.intent.llm_classifier import LLMIntentClassifier
        from app.models.llm_client import LLMClient

        classifier = LLMIntentClassifier(LLMClient(cfg), prompts_dir=cfg.PROMPTS_DIR)
        done = {"n": 0}

        def classify(question):
            done["n"] += 1
            if done["n"] % 10 == 0 or done["n"] == len(rows):
                log.info("classified %d/%d", done["n"], len(rows))
            return classifier.classify(question)
    result = evaluate(classify, rows)
    out = Path(cfg.EVAL_DIR) / "results" / f"intent_{args.method}_{args.split}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    for part in ["overall", "ar", "en", "mixed"]:
        if part in result:
            r = result[part]
            log.info("%-7s n=%3d accuracy=%.3f macro_f1=%.3f out_of_scope_f1=%.3f",
                     part, r["n"], r["accuracy"], r["macro_f1"], r["out_of_scope_f1"])
    log.info("%d errors; full results -> %s", len(result["errors"]), out)


def check_model(cfg, args):
    """Confirm the pinned generation model is installed and matches models.lock."""
    from app.models.llm_client import LLMClient, ModelUnavailableError

    try:
        digest = LLMClient(cfg).verify_model()
    except ModelUnavailableError as e:
        log.error("%s", e)
        raise SystemExit(1)
    log.info("OK: %s matches models.lock (%s)", cfg.LLM_MODEL, digest[:12])


def evaluate_retrieval(cfg, args):
    """Run the retrieval gold set for one or all methods and save the results."""
    from app.retrieval.evaluate import evaluate, load_gold
    from app.retrieval.factory import build_retriever
    from app.retrieval.retriever import METHODS

    methods = METHODS if args.method == "all" else (args.method,)
    retriever = build_retriever(cfg, with_embeddings=methods != ("bm25",))
    gold = load_gold(Path(cfg.EVAL_DIR) / "retrieval" / "gold.jsonl")
    out_dir = Path(cfg.EVAL_DIR) / "results"
    out_dir.mkdir(parents=True, exist_ok=True)
    for method in methods:
        result = evaluate(retriever, gold, method)
        out = out_dir / f"retrieval_{method}.json"
        out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        for part in ["overall", "ar", "en", "mixed"]:
            if part in result:
                r = result[part]
                log.info("%-10s %-7s n=%2d recall@5=%.3f recall@10=%.3f precision@5=%.3f",
                         method, part, r["n"], r["recall@5"], r["recall@10"], r["precision@5"])
        log.info("%-10s version leaks=%d, failures=%d -> %s",
                 method, result["version_leaks"], len(result["failures"]), out)


def search(cfg, args):
    """Show the top passages for one question, for manual checking."""
    from app.retrieval.factory import build_retriever

    retriever = build_retriever(cfg, with_embeddings=args.method != "bm25")
    for rank_no, chunk in enumerate(retriever.search(args.question, args.as_of, args.method, args.k), 1):
        snippet = " ".join(chunk["text"].split())[:160]
        log.info("%d. %s (p%s) %s", rank_no, chunk["chunk_id"], chunk["page"], snippet)


def evaluate_conflicts(cfg, args):
    """Score evidence validation on the planted conflict set and save the results."""
    from app.evidence.evaluate import evaluate_planted, load_planted

    result = evaluate_planted(load_planted(Path(cfg.EVAL_DIR) / "conflicts" / "planted.jsonl"))
    out = Path(cfg.EVAL_DIR) / "results" / "conflicts_planted.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    for key in ("cases", "detection_rate", "false_positive_rate", "resolution_accuracy",
                "status_accuracy", "all_checks_passed"):
        log.info("%-20s %s", key, result[key])
    for r in result["results"]:
        if not r["passed"]:
            log.warning("failed %s: %s %s", r["id"], r["description"], r["checks"])
    log.info("full results -> %s", out)


def conflict_report(cfg, args):
    """Validate the evidence for every gold question and report conflicts for the department."""
    from app.evidence.validator import validate_evidence
    from app.retrieval.evaluate import load_gold
    from app.retrieval.factory import build_retriever

    retriever = build_retriever(cfg, with_embeddings=args.method != "bm25")
    sources = {s["source_id"]: s for s in retriever.sources}
    found, statuses = {}, {}
    for g in load_gold(Path(cfg.EVAL_DIR) / "retrieval" / "gold.jsonl"):
        chunks = retriever.search(g["question"], g["as_of"], args.method, cfg.TOP_K)
        report = validate_evidence(g["intent"], g["question"], chunks, sources, g["as_of"])
        statuses[report["status"]] = statuses.get(report["status"], 0) + 1
        for c in report["conflicts"]:
            key = json.dumps([c["type"], c["kind"], c["chunks"]], sort_keys=True)
            entry = found.setdefault(key, {**c, "questions": []})
            entry["questions"].append(g["id"])
    conflicts = list(found.values())
    out_dir = Path(cfg.EVAL_DIR) / "results"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "conflict_report.json").write_text(
        json.dumps({"statuses": statuses, "conflicts": conflicts}, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = ["# conflict report for the Admission and Registration Deanship", "",
             f"Generated from {sum(statuses.values())} gold questions with {args.method} retrieval.", "",
             "| type | values by source | applies | rule | review | questions |", "|---|---|---|---|---|---|"]
    for c in conflicts:
        values = "; ".join(f"{s}: {v}" for s, v in c["values"].items())
        lines.append(f"| {c['type']}/{c['kind']} | {values} | {c['winner'] or 'UNRESOLVED'} | {c['rule']} "
                     f"| {', '.join(c['flag_for_review'])} | {', '.join(c['questions'])} |")
    if not conflicts:
        lines.append("| none found | | | | | |")
    (out_dir / "conflict_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    log.info("statuses: %s", statuses)
    log.info("%d distinct conflicts -> %s", len(conflicts), out_dir / "conflict_report.md")


def _parse_value(text):
    """Turn a command-line value into a bool, number or string."""
    if text.lower() in ("true", "false"):
        return text.lower() == "true"
    try:
        return float(text) if "." in text else int(text)
    except ValueError:
        return text


def run_rule(cfg, args):
    """Evaluate one rule from the library on a date, for manual checking."""
    from app.rules.calendar_rules import CalendarStore
    from app.rules.rule_engine import RuleEngine

    sources = load_sources(cfg)
    store = CalendarStore.from_dir(Path(cfg.PROCESSED_DIR) / "calendar", sources)
    engine = RuleEngine.from_file(cfg.RULES_FILE, store)
    inputs = dict(pair.split("=", 1) for pair in args.input)
    result = engine.run(args.rule_id, args.as_of, term_id=args.term,
                        **{k: _parse_value(v) for k, v in inputs.items()})
    log.info("%s on %s -> %s", result["rule_id"], result["as_of"], result["output"])
    log.info("details: %s", json.dumps(result["details"], ensure_ascii=False))
    log.info("sources: %s", ", ".join(f"{s['source_id']} ({s['section']})" for s in result["sources"]))


def rules_doc(cfg, args):
    """Write docs/rules.md from the rule library so the two never disagree."""
    library = json.loads(Path(cfg.RULES_FILE).read_text(encoding="utf-8"))
    lines = ["# rules", "",
             f"Generated from `{cfg.RULES_FILE}` by `python cli.py rules-doc`; edit the JSON, not this file.", "",
             "Every rule cites an institutional source, declares its inputs, and has boundary tests in",
             "`tests/test_rules.py`. A missing input returns `unknown`; nothing is filled with a default.",
             "Rules inform the student; they never take an official decision.", "",
             "## calendar rules", "",
             "Calendar rules read the academic calendar **in force on `as_of`**. When the question names",
             "no term, `current` rules use the term in progress (first term before it starts) and",
             "`upcoming` rules use the next term to start. The answer states which basis was used.", ""]
    for kind, title in (("calendar", None), ("regulation", "## regulation rules")):
        if title:
            lines += [title, ""]
        for r in (x for x in library if x["kind"] == kind):
            lines += [f"### {r['rule_id']}: {r['title']}", "",
                      f"- **source:** {'; '.join(s['source_id'] + ', ' + s['section'] for s in r['sources'])}",
                      f"- **inputs:** {', '.join(r['inputs'])}",
                      f"- **condition:** {r['condition']}",
                      f"- **outputs:** {', '.join(r['outputs'])}",
                      f"- **effective:** {r['effective_from']} to {r['effective_to'] or 'open'}"]
            if kind == "calendar":
                lines.append(f"- **calendar event:** `{r['event_code']}`, compared `{r['comparison']}`, term basis `{r['term_basis']}`")
            lines += [f"- **tests:** {', '.join(r['tests'])}", ""]
    lines += ["## notes", "",
              "- **Semester withdrawal:** the handbook says the request is made at least two weeks before",
              "  final exams (latest 2026-11-22 for the first term); the calendar sets 2026-11-19. The calendar",
              "  date is the stricter one and is the date the rule uses.",
              "- **Refunds:** only tuition for a term not yet started is refundable; administrative fees never are."]
    out = Path("docs") / "rules.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    log.info("%d rules -> %s", len(library), out)


def ask(cfg, args):
    """Answer one question through the pipeline and print the response."""
    from app.pipeline.factory import build_assistant
    from app.schemas.answer import validate_response

    clarification = dict(pair.split("=", 1) for pair in args.clarify)
    response = build_assistant(cfg).answer(args.question, args.as_of, clarification=clarification or None)
    errors = validate_response(response)
    log.info("status=%s intent=%s schema_errors=%s", response["status"], response["intent"], errors or "none")
    shown = {k: v for k, v in response.items() if not k.startswith("_")}
    log.info("response:\n%s", json.dumps(shown, ensure_ascii=False, indent=2))
    log.info("trace: %s", json.dumps(response.get("_trace", {}), ensure_ascii=False))


def generate_sample(cfg, args):
    """Run a spread of gold questions end to end and check every response against the schema."""
    from app.pipeline.factory import build_assistant
    from app.retrieval.evaluate import load_gold
    from app.schemas.answer import validate_response

    if args.file:
        picked = load_gold(args.file)
    else:
        gold = load_gold(Path(cfg.EVAL_DIR) / "retrieval" / "gold.jsonl")
        step = max(1, len(gold) // args.n)
        picked = gold[::step][: args.n]
    assistant = build_assistant(cfg)
    rows, statuses = [], {}
    for i, g in enumerate(picked, 1):
        response = assistant.answer(g["question"], g["as_of"])
        errors = validate_response(response)
        statuses[response["status"]] = statuses.get(response["status"], 0) + 1
        trace = response.get("_trace", {})
        checks = {}
        if "expected_status" in g:
            checks["status"] = response["status"] == g["expected_status"]
            text = json.dumps(response, ensure_ascii=False)
            checks["contains"] = all(m in text for m in g.get("must_contain", []))
        rows.append({"id": g["id"], "question": g["question"], "as_of": g["as_of"],
                     "expected_evidence": g.get("evidence"), "schema_errors": errors, "checks": checks,
                     "mode": trace.get("mode"), "verification_issues": trace.get("verification_issues", []),
                     "response": {k: v for k, v in response.items() if not k.startswith("_")},
                     "trace": response.get("_trace", {})})
        log.info("%d/%d %s %-22s mode=%-10s schema_errors=%d %s", i, len(picked), g["id"], response["status"],
                 trace.get("mode"), len(errors), checks or "")
    valid = sum(not r["schema_errors"] for r in rows)
    modes = {}
    for r in rows:
        modes[r["mode"]] = modes.get(r["mode"], 0) + 1
    out = Path(cfg.EVAL_DIR) / "results" / f"{args.out}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"schema_valid": valid, "n": len(rows), "statuses": statuses, "modes": modes,
                               "rows": rows}, ensure_ascii=False, indent=2), encoding="utf-8")
    passed = [r for r in rows if r["checks"] and all(r["checks"].values())]
    log.info("schema valid %d/%d, statuses %s, modes %s -> %s", valid, len(rows), statuses, modes, out)
    if any(r["checks"] for r in rows):
        log.info("expectation checks passed %d/%d", len(passed), len(rows))


def _report_md(title, summary, rows, frozen, set_path="evaluation/end_to_end/inquiries.jsonl"):
    """Write the human-readable Experiment 3 report."""
    o, ar, en = summary["overall"], summary["ar"], summary["en"]
    keys = [("status_accuracy", "status accuracy (all six)"), ("correct_refusal_rate", "correct refusal rate"),
            ("correct_refusal_exact_status", "correct refusal, exact status"), ("false_refusal_rate", "false refusal rate"),
            ("answer_correct_when_answered", "answer correct when answered"), ("end_to_end_correct", "end-to-end correct"),
            ("wrong_answers_shown", "wrong answers shown to a student"), ("grounded_claim_rate", "grounded claim rate (judged claims)"),
            ("unsupported_claim_rate", "unsupported claim rate (judged claims)"),
            ("model_claim_grounded_rate", "grounded rate, model sentences only"), ("claims_unverified", "claims needing human review"),
            ("citation_accuracy", "citation accuracy (judged citations)"), ("self_service_rate", "self-service rate")]
    lines = [f"# {title}", "", f"Set: `{set_path}`, sha256 `{frozen}`, {o['n']} inquiries.",
             "Automatic first-pass labels; see `docs/evaluation.md` for definitions and limits.", "",
             "| metric | overall | Arabic | English |", "|---|---|---|---|"]
    lines += [f"| {label} | {o[k]} | {ar[k]} | {en[k]} |" for k, label in keys]
    lines += ["", f"Response time (s): median {summary['seconds'].get('median')}, p90 {summary['seconds'].get('p90')}, "
              f"max {summary['seconds'].get('max')}. Reproducible on repeat: {summary.get('reproducible_rate')}.",
              f"Answer modes: {summary['modes']}", "", "## confusion (rows expected, columns returned)", "",
              "| expected \\ returned | " + " | ".join(s[:12] for s in summary["confusion"]) + " |",
              "|---" * (len(summary["confusion"]) + 1) + "|"]
    for e, cols in summary["confusion"].items():
        lines.append(f"| {e} | " + " | ".join(str(v) for v in cols.values()) + " |")
    lines += ["", "## every incorrect inquiry", "", "| id | lang | expected | returned | mode | problem |", "|---|---|---|---|---|---|"]
    for r in rows:
        if r["correct"]:
            continue
        problem = []
        if not r["status_ok"]:
            problem.append("wrong status")
        elif not r["facts_ok"]:
            problem.append("required fact missing")
        if r["forbidden"]:
            problem.append(f"forbidden: {', '.join(r['forbidden'])}")
        lines.append(f"| {r['item']['id']} | {r['item']['language']} | {r['item']['expected_status']} | "
                     f"{r['response']['status']} | {r['mode']} | {'; '.join(problem)} |")
    return "\n".join(lines) + "\n"


def evaluate_e2e(cfg, args):
    """Experiment 3: run the frozen end-to-end set and score status, refusals, claims and citations."""
    import csv

    from app.pipeline.evaluate import load_jsonl, review_sheet, run_set, score_row, summarize
    from app.pipeline.factory import build_assistant

    path = Path(cfg.EVAL_DIR) / "end_to_end" / f"{args.set}.jsonl"
    frozen = hashlib.sha256(path.read_bytes()).hexdigest()
    hashes = {}
    for line in (Path(cfg.EVAL_DIR) / "end_to_end" / "FROZEN").read_text().splitlines():
        parts = line.split()
        if len(parts) == 2 and parts[1].endswith(".jsonl"):
            hashes[parts[1]] = parts[0]
    expected = hashes.get(path.name)
    if frozen != expected:
        log.error("%s is not frozen or changed after freezing (sha256 %s, frozen %s); refusing to score",
                  path.name, frozen[:12], (expected or "none")[:12])
        return
    items = load_jsonl(path)[: args.limit or None]
    assistant = build_assistant(cfg)
    assistant.escalation_log = Path(cfg.EVAL_DIR) / "results" / f"{args.out}_escalations.jsonl"  # keep the real log clean
    assistant.escalation_log.unlink(missing_ok=True)
    chunk_text = {c["chunk_id"]: c["text"] for c in assistant.retriever.chunks}
    rows = []
    for i, row in enumerate(run_set(assistant, items, chunk_text, repeat=not args.no_repeat), 1):
        score_row(row, chunk_text)
        rows.append(row)
        log.info("%3d/%d %s %-22s -> %-22s %s %5.1fs", i, len(items), row["item"]["id"], row["item"]["expected_status"],
                 row["response"]["status"], "ok " if row["correct"] else "BAD", row["seconds"])
    summary = summarize(rows)
    results = Path(cfg.EVAL_DIR) / "results"
    results.mkdir(parents=True, exist_ok=True)
    stored = [{"id": r["item"]["id"], "item": r["item"], "seconds": r["seconds"], "reproducible": r.get("reproducible"),
               "status_ok": r["status_ok"], "facts_ok": r["facts_ok"], "forbidden": r["forbidden"], "correct": r["correct"],
               "mode": r["mode"], "claims": r["claims"], "citations": r["citations"],
               "response": {k: v for k, v in r["response"].items() if not k.startswith("_")},
               "trace": r["response"].get("_trace", {})} for r in rows]
    (results / f"{args.out}.json").write_text(json.dumps({"set_sha256": frozen, "summary": summary, "rows": stored},
                                                         ensure_ascii=False, indent=2), encoding="utf-8")
    (results / f"{args.out}.md").write_text(_report_md(f"Experiment 3: {args.out}", summary, rows, frozen[:12],
                                                       f"evaluation/end_to_end/{path.name}"),
                                            encoding="utf-8")
    sheet = review_sheet(rows)
    with (results / f"{args.out}_review.csv").open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(sheet[0]) if sheet else ["id"])
        writer.writeheader()
        writer.writerows(sheet)
    o = summary["overall"]
    log.info("status accuracy %s | correct refusal %s | false refusal %s | wrong answers shown %s | grounded %s "
             "(unverified %s) | citation accuracy %s | median %ss", o["status_accuracy"], o["correct_refusal_rate"],
             o["false_refusal_rate"], o["wrong_answers_shown"], o["grounded_claim_rate"], o["claims_unverified"],
             o["citation_accuracy"], summary["seconds"].get("median"))
    log.info("-> %s.json, %s.md, %s_review.csv in %s", args.out, args.out, args.out, results)


def evaluate_adversarial(cfg, args):
    """Run the adversarial cases; expected behaviour is refusal, the correct status or escalation."""
    from app.documents.injection import injection_signals
    from app.pipeline.evaluate import InjectingRetriever, load_jsonl, score_adversarial
    from app.pipeline.factory import build_assistant

    cases = load_jsonl(Path(cfg.EVAL_DIR) / "adversarial" / "cases.jsonl")
    assistant = build_assistant(cfg)
    assistant.escalation_log = Path(cfg.EVAL_DIR) / "results" / f"{args.out}_escalations.jsonl"
    assistant.escalation_log.unlink(missing_ok=True)
    base_retriever, base_sources = assistant.retriever, assistant.sources_by_id
    rows = []
    for case in cases:
        signals = injection_signals(case["inject"]) if case.get("inject") else []
        if case.get("inject"):
            # Bypass the ingest scanner on purpose: the pipeline must stay safe even if a bad page got in.
            assistant.retriever = InjectingRetriever(base_retriever, case["inject"])
            assistant.sources_by_id = {**base_sources, InjectingRetriever.SOURCE["source_id"]: InjectingRetriever.SOURCE}
        response = assistant.answer(case["question"], case["as_of"])
        assistant.retriever, assistant.sources_by_id = base_retriever, base_sources
        passed, reasons = score_adversarial(case, response, signals)
        rows.append({"id": case["id"], "kind": case["kind"], "question": case["question"], "passed": passed,
                     "reasons": reasons, "scanner_signals": signals, "status": response["status"],
                     "answer": response["answer"], "sources": response.get("sources", []),
                     "trace": response.get("_trace", {})})
        log.info("%s %-18s %-22s %s %s", case["id"], case["kind"], response["status"], "PASS" if passed else "FAIL",
                 "; ".join(reasons))
    out = Path(cfg.EVAL_DIR) / "results" / f"{args.out}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"passed": sum(r["passed"] for r in rows), "n": len(rows), "rows": rows},
                              ensure_ascii=False, indent=2), encoding="utf-8")
    log.info("adversarial passed %d/%d -> %s", sum(r["passed"] for r in rows), len(rows), out)


def build_parser():
    """Define the command-line interface."""
    parser = argparse.ArgumentParser(description="Admission assistant tasks")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("fetch", help="download the source documents")
    sub.add_parser("peek", help="extract text to data/processed/peek for inspection")
    sub.add_parser("build-calendar", help="parse calendars into structured events")
    sub.add_parser("ingest", help="chunk all sources into data/processed/chunks.jsonl")
    sub.add_parser("check-model", help="verify the pinned model against models.lock")
    ev = sub.add_parser("evaluate-intent", help="score an intent classifier")
    ev.add_argument("--method", default="keyword", choices=["keyword", "llm"])
    ev.add_argument("--split", default="test", choices=["dev", "test", "all"])
    er = sub.add_parser("evaluate-retrieval", help="score retrieval on the gold set")
    er.add_argument("--method", default="all", choices=["bm25", "embeddings", "hybrid", "all"])
    se = sub.add_parser("search", help="show the top passages for one question")
    se.add_argument("question")
    se.add_argument("--as-of", required=True, help="YYYY-MM-DD, the date the question is about")
    se.add_argument("--method", default="hybrid", choices=["bm25", "embeddings", "hybrid"])
    se.add_argument("--k", type=int, default=5)
    sub.add_parser("evaluate-conflicts", help="score evidence validation on planted conflicts")
    cr = sub.add_parser("conflict-report", help="report source conflicts found for gold questions")
    cr.add_argument("--method", default="hybrid", choices=["bm25", "embeddings", "hybrid"])
    ru = sub.add_parser("rule", help="evaluate one rule on a date")
    ru.add_argument("rule_id")
    ru.add_argument("--as-of", required=True, help="YYYY-MM-DD")
    ru.add_argument("--term", default=None, help="e.g. 1448-T1; resolved from the date when omitted")
    ru.add_argument("--input", action="append", default=[], help="key=value, repeatable")
    sub.add_parser("rules-doc", help="write docs/rules.md from the rule library")
    ak = sub.add_parser("ask", help="answer one question through the pipeline")
    ak.add_argument("question")
    ak.add_argument("--as-of", required=True, help="YYYY-MM-DD, the date the question is about")
    ak.add_argument("--clarify", action="append", default=[],
                    help="clarification reply, e.g. withdrawal_scope=semester or degree_level=master")
    gs = sub.add_parser("generate-sample", help="run gold questions end to end and check the schema")
    gs.add_argument("--n", type=int, default=10)
    gs.add_argument("--file", default=None, help="question file with expected_status, e.g. evaluation/generation/smoke.jsonl")
    gs.add_argument("--out", default="generation_sample", help="results file name in evaluation/results/")
    e2e = sub.add_parser("evaluate-e2e", help="Experiment 3 on the frozen end-to-end set")
    e2e.add_argument("--out", default="e2e_v1", help="results name in evaluation/results/")
    e2e.add_argument("--set", default="inquiries", choices=["inquiries", "holdout"],
                     help="inquiries: the 100-inquiry set; holdout: 40 inquiries frozen before the step 11b fixes")
    e2e.add_argument("--limit", type=int, default=0, help="run only the first N inquiries (smoke run)")
    e2e.add_argument("--no-repeat", action="store_true", help="skip the reproducibility re-run")
    adv = sub.add_parser("evaluate-adversarial", help="run the adversarial cases")
    adv.add_argument("--out", default="adversarial_v1", help="results name in evaluation/results/")
    add = sub.add_parser("add-source", help="register a new document version")
    add.add_argument("--file", required=True, help="path to the new PDF or HTML file")
    add.add_argument("--source-id", required=True, help="e.g. CALENDAR-1449")
    add.add_argument("--title", required=True)
    add.add_argument("--type", required=True,
                     choices=["regulation", "calendar", "program_requirements", "procedure", "faq"])
    add.add_argument("--authority", required=True, type=int, help="1 = highest")
    add.add_argument("--version", required=True)
    add.add_argument("--effective-from", required=True, help="YYYY-MM-DD")
    add.add_argument("--effective-to", default=None, help="YYYY-MM-DD, optional")
    add.add_argument("--supersedes", default=None, help="source_id this version replaces")
    add.add_argument("--language", default="ar", choices=["ar", "en"])
    add.add_argument("--url", default=None, help="public URL, so 'fetch' can restore the file")
    return parser


COMMANDS = {"fetch": fetch, "peek": peek, "build-calendar": build_calendar,
            "ingest": ingest, "add-source": add_source_cmd,
            "evaluate-intent": evaluate_intent, "check-model": check_model,
            "evaluate-retrieval": evaluate_retrieval, "search": search,
            "evaluate-conflicts": evaluate_conflicts, "conflict-report": conflict_report,
            "rule": run_rule, "rules-doc": rules_doc,
            "ask": ask, "generate-sample": generate_sample,
            "evaluate-e2e": evaluate_e2e, "evaluate-adversarial": evaluate_adversarial}


def main():
    """Parse arguments and run the chosen command."""
    args = build_parser().parse_args()
    cfg = config_by_name["default"]
    logging.basicConfig(level=cfg.LOG_LEVEL,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    from app.models.seed import set_seed

    set_seed(cfg.SEED)
    COMMANDS[args.command](cfg, args)


if __name__ == "__main__":
    main()
