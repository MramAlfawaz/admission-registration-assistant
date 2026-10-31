import csv
import json
import tempfile
from pathlib import Path

from app.pipeline.ratings import CRITERIA, SHEET_FIELDS, efficiency, sample_answers, score_claim_review, score_ratings


def _result_file(tmp, rows):
    p = Path(tmp) / "r.json"
    p.write_text(json.dumps({"rows": rows}, ensure_ascii=False), encoding="utf-8")
    return p


def _row(i, status, lang="ar", correct=True, seconds=1.0):
    return {"id": f"E{i:03d}", "item": {"language": lang, "question": "q", "as_of": "2026-10-14"}, "correct": correct,
            "seconds": seconds, "claims": [], "response": {"status": status, "answer": "a", "sources": []}}


def test_sample_keeps_a_quota_of_each_non_answer_status():
    with tempfile.TemporaryDirectory() as tmp:
        rows = [_row(i, "ANSWERABLE") for i in range(30)] + [_row(100 + i, s) for i, s in enumerate(
            ["CLARIFICATION_REQUIRED"] * 3 + ["STAFF_REVIEW_REQUIRED"] * 3 + ["OUT_OF_SCOPE"] * 2 + ["INSUFFICIENT_EVIDENCE"] * 2)]
        picked = sample_answers([_result_file(tmp, rows)])
        assert len(picked) == 20 and sum(r["response"]["status"] == "ANSWERABLE" for r in picked) == 14
        assert picked == sample_answers([_result_file(tmp, rows)])  # fixed seed


def test_scores_only_fully_rated_rows():
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "s.csv"
        with open(p, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=SHEET_FIELDS)
            w.writeheader()
            w.writerow({"id": "E1", "language": "ar", "status": "ANSWERABLE", **{c: "5" for c in CRITERIA}, "rater": "MA"})
            w.writerow({"id": "E2", "language": "en", "status": "OUT_OF_SCOPE", **{c: "2" for c in CRITERIA}, "rater": "MA"})
            w.writerow({"id": "E3", "language": "ar", "status": "ANSWERABLE", "correctness": "4"})
        s = score_ratings(p)
        assert s["rated"] == 2 and s["overall"]["correctness"]["mean"] == 3.5 and s["ar"]["clarity"]["mean"] == 5
        assert [r["id"] for r in s["low_scores"]] == ["E2"]


def test_claim_review_agreement():
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "c.csv"
        with open(p, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["id", "language", "type", "auto_label", "claim", "evidence", "human_label", "note"])
            w.writeheader()
            w.writerow({"auto_label": "unverified", "human_label": "grounded"})
            w.writerow({"auto_label": "unverified", "human_label": "unsupported"})
            w.writerow({"auto_label": "grounded", "human_label": "Grounded"})
            w.writerow({"auto_label": "unsupported", "human_label": "grounded"})
        s = score_claim_review(p)
        assert s["english_grounded_rate"] == 0.5 and s["auto_vs_human_agreement"] == 0.5


def test_efficiency_splits_answers_and_refusals():
    with tempfile.TemporaryDirectory() as tmp:
        f = _result_file(tmp, [_row(1, "ANSWERABLE", seconds=30), _row(2, "ANSWERABLE", seconds=40),
                               _row(3, "OUT_OF_SCOPE", correct=True, seconds=1)])
        e = efficiency(f, [f])
        assert e["answered"]["median"] == 35 and e["non_answers"]["median"] == 1 and e["self_service"]["r.json"] == round(2 / 3, 3)
