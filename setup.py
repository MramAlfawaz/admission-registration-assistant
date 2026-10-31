"""Bootstrap a fresh clone and check it is the environment the results were measured in.

    python setup.py              every step (Ollama must be running with the pinned model)
    python setup.py --skip-llm   every step except the Ollama check (used when building images)

Steps, each stopping with a clear message on failure (Development Standards 1.1 and 1.9):
 0. interpreter matches .python-version
 1. installed packages match requirements.txt exactly
 2. .env created from .env.example
 3. source documents downloaded, calendar parsed, chunks built; chunk hash compared
 4. pinned embedding model downloaded and passage vectors cached (otherwise the first
    question would download about 470 MB with no sign of progress)
 5. pinned generation model checked against models.lock

This is a plain script, not a packaging file: do not run "pip install .".
"""
import argparse
import hashlib
import json
import logging
import shutil
import subprocess
import sys
from importlib import metadata
from pathlib import Path

ROOT = Path(__file__).resolve().parent
# The chunks every reported number was measured on (README, "what it produces today").
EXPECTED_CHUNKS = (186, "9e6394386f2f")

log = logging.getLogger("setup")


class BootstrapError(Exception):
    """A step failed; the message says what to do."""


def check_python():
    """Step 0: the interpreter must match .python-version (major and minor; patch is a warning)."""
    wanted = (ROOT / ".python-version").read_text(encoding="utf-8").strip()
    have = ".".join(str(x) for x in sys.version_info[:3])
    if have.split(".")[:2] != wanted.split(".")[:2]:
        raise BootstrapError(f"Python {wanted} is required, this is {have}. Create the environment with "
                             f"python{'.'.join(wanted.split('.')[:2])} -m venv .venv "
                             "(see docs/troubleshooting/python-and-packages.md).")
    if have != wanted:
        log.warning("Python %s found, %s pinned; continuing (same minor version)", have, wanted)
    log.info("step 0 ok: Python %s", have)


def _base(version):
    return version.split("+")[0]  # 2.2.2+cpu is the CPU build of 2.2.2


def check_packages():
    """Step 1: every line of requirements.txt must be installed at exactly that version."""
    problems = []
    for line in (ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines():
        line = line.split("#")[0].strip()
        if not line:
            continue
        name, _, pinned = line.partition("==")
        try:
            installed = metadata.version(name)
        except metadata.PackageNotFoundError:
            problems.append(f"{name} missing (pinned {pinned})")
            continue
        if _base(installed) != pinned:
            problems.append(f"{name} {installed} installed, {pinned} pinned")
    if problems:
        raise BootstrapError("packages differ from requirements.txt:\n  " + "\n  ".join(problems) +
                             "\nRun: pip install -r requirements.txt")
    log.info("step 1 ok: all pinned packages installed")


def make_env():
    """Step 2: create .env from the committed template if it does not exist."""
    env, example = ROOT / ".env", ROOT / ".env.example"
    if not example.exists():
        raise BootstrapError(".env.example is missing; restore it with: git checkout .env.example")
    if env.exists():
        log.info("step 2 ok: .env already present (left unchanged)")
    else:
        shutil.copy(example, env)
        log.info("step 2 ok: .env created from .env.example")


def _cli(*args):
    result = subprocess.run([sys.executable, "cli.py", *args], cwd=ROOT)
    if result.returncode != 0:
        raise BootstrapError(f"'python cli.py {' '.join(args)}' failed; see the messages above")


def build_data():
    """Step 3: download the documents, parse the calendar, build the chunks; compare the chunk hash."""
    _cli("fetch")
    sources = json.loads((ROOT / "data" / "sources.json").read_text(encoding="utf-8"))
    missing = [s["filename"] for s in sources if not (ROOT / "data" / "raw" / s["filename"]).exists()]
    if missing:
        raise BootstrapError(f"documents not downloaded: {', '.join(missing)}. The university site may be "
                             "down or have moved them; see docs/troubleshooting/documents-and-data.md.")
    _cli("build-calendar")
    _cli("ingest")
    body = (ROOT / "data" / "processed" / "chunks.jsonl").read_bytes()
    count, digest = body.count(b"\n"), hashlib.sha256(body).hexdigest()[:12]
    if (count, digest) != EXPECTED_CHUNKS:
        log.warning("chunks differ from the ones the results were measured on: %d chunks, sha256 %s "
                    "(expected %d, %s). The documents on the university site have probably changed; "
                    "the application works, but reported numbers may not reproduce. "
                    "See docs/troubleshooting/documents-and-data.md.", count, digest, *EXPECTED_CHUNKS)
    else:
        log.info("step 3 ok: %d chunks, sha256 %s (as measured)", count, digest)


def prepare_embeddings():
    """Step 4: download the pinned embedding model and cache the passage vectors."""
    sys.path.insert(0, str(ROOT))
    from config.config import BaseConfig
    from app.retrieval.factory import build_retriever

    try:
        build_retriever(BaseConfig, with_embeddings=True)
    except Exception as e:  # network, disk or a changed model repository
        raise BootstrapError(f"embedding model could not be prepared ({type(e).__name__}: {e}); "
                             "see docs/troubleshooting/models.md") from e
    log.info("step 4 ok: embedding model ready, passage vectors cached")


def check_llm():
    """Step 5: the generation model in Ollama must match models.lock."""
    _cli("check-model")
    log.info("step 5 ok: generation model matches models.lock")


def main():
    """Run every bootstrap step in order and stop at the first failure."""
    parser = argparse.ArgumentParser(description="bootstrap a fresh clone")
    parser.add_argument("--skip-llm", action="store_true", help="skip the Ollama model check (step 5)")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    steps = [check_python, check_packages, make_env, build_data, prepare_embeddings]
    if not args.skip_llm:
        steps.append(check_llm)
    try:
        for step in steps:
            step()
    except BootstrapError as e:
        log.error("%s", e)
        raise SystemExit(1)
    log.info("bootstrap passed%s", " (generation model not checked)" if args.skip_llm else "")


if __name__ == "__main__":
    main()
