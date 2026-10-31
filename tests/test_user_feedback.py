"""User evaluation summary: students and staff reported separately (brief, Experiment 5)."""
import csv
import tempfile
from pathlib import Path

from app.pipeline.ratings import FEEDBACK_FIELDS, score_feedback

ROOT = Path(__file__).resolve().parents[1]


def _write(rows):
    path = Path(tempfile.mkdtemp()) / "feedback.csv"
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FEEDBACK_FIELDS)
        w.writeheader()
        w.writerows(rows)
    return path


def test_students_and_staff_are_reported_separately():
    base = {"date": "2026-11-01", "tasks_given": "5", "comment": ""}
    s = score_feedback(_write([
        {**base, "participant": "S1", "group": "student", "tasks_completed": "5", "ease": "5", "clarity": "4", "sources": "4", "trust": "3"},
        {**base, "participant": "S2", "group": "student", "tasks_completed": "4", "ease": "3", "clarity": "4", "sources": "5", "trust": "5"},
        {**base, "participant": "T1", "group": "staff", "tasks_completed": "5", "ease": "4", "clarity": "4", "sources": "5",
         "trust": "4", "defensible": "3", "comment": "wants the article number"},
    ]))
    assert s["participants"] == 3 and s["student"]["n"] == 2 and s["staff"]["n"] == 1
    assert s["student"]["ease"] == {"n": 2, "mean": 4, "sd": 1.41}
    assert s["student"]["defensible"]["n"] == 0 and s["staff"]["defensible"]["mean"] == 3
    assert s["student"]["task_completion"] == 0.9
    assert s["comments"] == [{"group": "staff", "comment": "wants the article number"}]


def test_committed_template_has_the_expected_columns():
    with (ROOT / "evaluation" / "user_evaluation" / "feedback.csv").open(encoding="utf-8-sig") as f:
        assert next(csv.reader(f)) == FEEDBACK_FIELDS
