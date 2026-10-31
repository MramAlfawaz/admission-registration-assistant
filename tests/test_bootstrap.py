"""The bootstrap script and the pins it checks (Development Standards 1.1)."""
from pathlib import Path

import setup

ROOT = Path(__file__).resolve().parents[1]


def test_every_requirement_is_pinned_exactly():
    lines = [l.strip() for l in (ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines() if l.strip()]
    assert lines and all("==" in l and ">" not in l and "<" not in l for l in lines)


def test_cpu_build_of_torch_counts_as_the_pinned_version():
    assert setup._base("2.2.2+cpu") == "2.2.2" and setup._base("1.26.4") == "1.26.4"


def test_expected_chunks_match_the_readme():
    count, digest = setup.EXPECTED_CHUNKS
    assert f"{count}, identical on every run (sha256 `{digest}`)" in (ROOT / "README.md").read_text(encoding="utf-8")


def test_models_lock_pins_both_models():
    lock = (ROOT / "models.lock").read_text(encoding="utf-8")
    assert "qwen2.5:3b" in lock and "intfloat/multilingual-e5-small" in lock


def test_processed_chunks_fixture_gives_real_chunks(processed_chunks):
    assert len(processed_chunks) == setup.EXPECTED_CHUNKS[0]
    assert {"chunk_id", "source_id", "text"} <= set(processed_chunks[0])
