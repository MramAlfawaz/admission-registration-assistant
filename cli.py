"""Run project tasks from the command line."""
import argparse
import json
import logging
import time
from pathlib import Path

import requests

from config.config import config_by_name

log = logging.getLogger("cli")


def load_sources(cfg):
    """Read the sources file."""
    return json.loads(Path(cfg.SOURCES_FILE).read_text(encoding="utf-8"))


def fetch(cfg):
    """Download every source listed in the sources file into the raw folder."""
    raw = Path(cfg.RAW_DIR)
    raw.mkdir(parents=True, exist_ok=True)
    headers = {"User-Agent": "Mozilla/5.0 (admission-registration-assistant)"}
    for s in load_sources(cfg):
        target = raw / s["filename"]
        if target.exists():
            log.info("skip %s (already downloaded)", s["source_id"])
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


def peek(cfg):
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


def build_calendar(cfg):
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


COMMANDS = {"fetch": fetch, "peek": peek, "build-calendar": build_calendar}


def main():
    """Parse arguments and run the chosen command."""
    parser = argparse.ArgumentParser(description="Admission assistant tasks")
    parser.add_argument("command", choices=COMMANDS)
    args = parser.parse_args()

    cfg = config_by_name["default"]
    logging.basicConfig(level=cfg.LOG_LEVEL,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    COMMANDS[args.command](cfg)


if __name__ == "__main__":
    main()
