"""Run project tasks from the command line."""
import argparse
import json
import logging
import time
from pathlib import Path

import requests

from config.config import config_by_name

log = logging.getLogger("cli")


def fetch(cfg):
    """Download every source listed in the sources file into the raw folder."""
    raw = Path(cfg.RAW_DIR)
    raw.mkdir(parents=True, exist_ok=True)
    sources = json.loads(Path(cfg.SOURCES_FILE).read_text(encoding="utf-8"))
    headers = {"User-Agent": "Mozilla/5.0 (admission-registration-assistant)"}
    for s in sources:
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


def main():
    """Parse arguments and run the chosen command."""
    parser = argparse.ArgumentParser(description="Admission assistant tasks")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("fetch", help="download the source documents")
    args = parser.parse_args()

    cfg = config_by_name["default"]
    logging.basicConfig(level=cfg.LOG_LEVEL,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    if args.command == "fetch":
        fetch(cfg)


if __name__ == "__main__":
    main()
