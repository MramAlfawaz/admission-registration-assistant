import json
from pathlib import Path

import pytest

from app.documents.version_selector import current_version, in_force

ROOT = Path(__file__).resolve().parent.parent
SOURCES = json.loads((ROOT / "data" / "sources.json").read_text(encoding="utf-8"))
CASES = json.loads((ROOT / "evaluation" / "version_selection" / "cases.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("case", CASES, ids=[c["id"] for c in CASES])
def test_version_by_date(case):
    chosen = current_version(SOURCES, case["family"], case["as_of"])
    assert (chosen["source_id"] if chosen else None) == case["expected"]


def test_newest_is_not_chosen_for_past_date():
    chosen = current_version(SOURCES, "PROGRAMS-GUIDE", "2026-03-01")
    assert chosen["version"] == "1447"


def test_effective_to_is_inclusive():
    src = {"effective_from": "2026-01-01", "effective_to": "2026-01-31"}
    assert in_force(src, "2026-01-31") and not in_force(src, "2026-02-01")


def test_overlapping_versions_raise():
    a = {"source_id": "X-1", "effective_from": "2026-01-01", "effective_to": None}
    b = {"source_id": "X-2", "effective_from": "2026-06-01", "effective_to": None}
    with pytest.raises(ValueError):
        current_version([a, b], "X", "2026-07-01")
