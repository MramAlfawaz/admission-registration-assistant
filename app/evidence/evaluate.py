"""Score evidence validation on the planted conflict set."""
import json
from pathlib import Path

from app.evidence.validator import validate_evidence


def load_planted(path):
    """Read planted cases; each carries its own sources, chunks and expectation."""
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line]


def run_case(case):
    """Validate one planted case and compare it with its expectation."""
    sources = {s["source_id"]: s for s in case["sources"]}
    report = validate_evidence(case["intent"], case["question"], case["chunks"], sources, case["as_of"])
    exp, conflicts = case["expected"], report["conflicts"]
    first = conflicts[0] if conflicts else {}
    checks = {"conflict": bool(conflicts) == exp["conflict"], "status": report["status"] == exp["status"]}
    if exp["conflict"]:
        checks["resolution"] = first.get("winner") == exp["winner"] and first.get("rule") == exp["rule"]
    if "rejected" in exp:
        checks["currency"] = [r["chunk_id"] for r in report["rejected_not_current"]] == exp["rejected"]
    if "off_topic" in exp:
        checks["relevance"] = [r["chunk_id"] for r in report["off_topic"]] == exp["off_topic"]
    if "missing" in exp:
        checks["completeness"] = report["missing_source_types"] == exp["missing"]
    return {"id": case["id"], "description": case["description"], "passed": all(checks.values()),
            "checks": checks, "status": report["status"],
            "conflicts": [{k: c[k] for k in ("type", "kind", "values", "winner", "rule")} for c in conflicts]}


def evaluate_planted(cases):
    """Return detection rate, false-positive rate, resolution accuracy and per-case results."""
    results = [run_case(c) for c in cases]
    planted = [r for r, c in zip(results, cases) if c["expected"]["conflict"]]
    clean = [r for r, c in zip(results, cases) if not c["expected"]["conflict"]]
    detected = [r for r in planted if r["conflicts"]]

    def rate(part, whole):
        return round(len(part) / len(whole), 4) if whole else None

    return {
        "cases": len(results),
        "detection_rate": rate(detected, planted),
        "false_positive_rate": rate([r for r in clean if r["conflicts"]], clean),
        "resolution_accuracy": rate([r for r in detected if r["checks"].get("resolution")], detected),
        "status_accuracy": rate([r for r in results if r["checks"]["status"]], results),
        "all_checks_passed": rate([r for r in results if r["passed"]], results),
        "results": results,
    }
