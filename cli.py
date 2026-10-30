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

    chunks = []
    for s in load_sources(cfg):
        part = build_chunks(s, cfg.RAW_DIR)
        log.info("%s: %d chunks", s["source_id"], len(part))
        chunks.extend(part)
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

    if args.method == "keyword":
        from app.intent.keyword_baseline import classify
    else:
        log.error("unknown method: %s", args.method)
        return
    split = None if args.split == "all" else args.split
    rows = load_questions(Path(cfg.EVAL_DIR) / "intent" / "questions.jsonl", split)
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


def build_parser():
    """Define the command-line interface."""
    parser = argparse.ArgumentParser(description="Admission assistant tasks")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("fetch", help="download the source documents")
    sub.add_parser("peek", help="extract text to data/processed/peek for inspection")
    sub.add_parser("build-calendar", help="parse calendars into structured events")
    sub.add_parser("ingest", help="chunk all sources into data/processed/chunks.jsonl")
    ev = sub.add_parser("evaluate-intent", help="score an intent classifier")
    ev.add_argument("--method", default="keyword", choices=["keyword"])
    ev.add_argument("--split", default="test", choices=["dev", "test", "all"])
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
            "evaluate-intent": evaluate_intent}


def main():
    """Parse arguments and run the chosen command."""
    args = build_parser().parse_args()
    cfg = config_by_name["default"]
    logging.basicConfig(level=cfg.LOG_LEVEL,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    COMMANDS[args.command](cfg, args)


if __name__ == "__main__":
    main()
