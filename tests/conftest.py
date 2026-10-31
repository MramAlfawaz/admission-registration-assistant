"""Shared test setup (Development Standards, Part 3).

- The repository root is put on the import path, so `python -m pytest` works from a fresh
  clone without installing anything.
- Tests never call Ollama, download a model or read the clock: model clients are fakes
  (`tests/test_generation.py`), dates are passed in, and fixtures are excerpts of the real
  documents (`tests/fixtures/`).
- Tests that need the processed data skip with an instruction when `python cli.py ingest` has
  not been run; the `processed_chunks` fixture below does the same for new tests.
"""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture
def processed_chunks():
    """The chunks built by 'python cli.py ingest', or a skip with the command to run."""
    path = ROOT / "data" / "processed" / "chunks.jsonl"
    if not path.exists():
        pytest.skip("run 'python cli.py fetch', 'build-calendar' and 'ingest' first")
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
