import json
from pathlib import Path

import pytest

from app.evidence.contradiction import find_conflicts, resolve
from app.evidence.currency_checker import check_currency
from app.evidence.evaluate import evaluate_planted, load_planted
from app.evidence.facts import Fact, extract_facts, same_value
from app.evidence.relevance import filter_relevant
from app.evidence.subject import extract_subject
from app.evidence.validator import validate_evidence

ROOT = Path(__file__).resolve().parent.parent


def src(sid, auth, frm, status="approved", to=None, dtype="faq"):
    return {"source_id": sid, "authority_level": auth, "effective_from": frm,
            "effective_to": to, "status": status, "document_type": dtype}


def fact(sid, value, kind="study_duration"):
    return Fact("duration", kind, value, {"degree": "master", "program": None, "term": None}, sid, f"{sid}#1")


def test_nearest_degree_wins():
    text = "كم مدة الدراسة لمرحلتي الماجستير والدبلوم العالي؟ مدة الدراسة في برامج الماجستير:"
    assert extract_subject(text)["degree"] == "master"


def test_fact_extraction_types():
    chunk = {"chunk_id": "X#1", "source_id": "X", "text": (
        "مدة الدراسة: عامان دراسيان. رسم التقديم 100 ريال. يحرم الطالب إذا قلت نسبة حضوره عن 75%. "
        "متطلبات التخرج بمعدل تراكمي لا يقل عن 5 من3.75")}
    found = {(f.type, f.kind, f.value) for f in extract_facts(chunk)}
    assert ("duration", "study_duration", 4) in found
    assert ("money", "application", 100) in found
    assert ("percent", "attendance", 75) in found
    assert ("gpa", "graduation", 3.75) in found


def test_iso_and_arabic_dates_compare_equal():
    iso = [f for f in extract_facts({"chunk_id": "A", "source_id": "A", "text": "آخر موعد للاعتذار 2026-11-19"})][0]
    ar = [f for f in extract_facts({"chunk_id": "B", "source_id": "B", "text": "آخر موعد للاعتذار 19 نوفمبر 2026"})][0]
    assert same_value(iso.value, ar.value)


def test_currency_rejects_out_of_force():
    sources = {"OLD": src("OLD", 3, "2025-08-01", to="2026-07-31"), "NEW": src("NEW", 3, "2026-08-01")}
    current, rejected = check_currency([{"chunk_id": "OLD#1", "source_id": "OLD"},
                                        {"chunk_id": "NEW#1", "source_id": "NEW"}], sources, "2026-10-14")
    assert [c["chunk_id"] for c in current] == ["NEW#1"] and rejected[0]["chunk_id"] == "OLD#1"


def test_relevance_drops_other_situation():
    chunks = [{"chunk_id": "R#11", "text": "لا يحق للطالب المعتذر استعادة الرسوم"},
              {"chunk_id": "F#20", "text": "استرداد الرسوم عند الانسحاب من البرنامج"}]
    relevant, off = filter_relevant(chunks, "SEMESTER_WITHDRAWAL")
    assert [c["chunk_id"] for c in relevant] == ["R#11"] and off[0]["chunk_id"] == "F#20"


def test_resolution_rules():
    s = {"REG": src("REG", 1, "2024-08-01"), "FAQ": src("FAQ", 5, "2024-09-01"),
         "OLD": src("OLD", 1, "2024-08-01", status="superseded"),
         "P1": src("P1", 4, "2025-08-23"), "P2": src("P2", 4, "2026-09-01"),
         "A": src("A", 5, None), "B": src("B", 5, None)}
    assert resolve([fact("FAQ", 4), fact("REG", 2)], s)["rule"] == "authority"
    assert resolve([fact("OLD", 4), fact("REG", 2)], s)["winner"] == "REG"
    assert resolve([fact("P1", 4), fact("P2", 2)], s)["winner"] == "P2"
    unresolved = resolve([fact("A", 4), fact("B", 2)], s)
    assert unresolved["winner"] is None and unresolved["rule"] == "unresolved"


def test_same_source_never_conflicts_with_itself():
    assert find_conflicts([fact("GUIDE", 4), fact("GUIDE", 2)]) == []


def test_unresolved_conflict_blocks_answer():
    sources = {"A": src("A", 5, None), "B": src("B", 5, None)}
    chunks = [{"chunk_id": "A#1", "source_id": "A", "text": "رسم التقديم 100 ريال"},
              {"chunk_id": "B#1", "source_id": "B", "text": "رسم التقديم 200 ريال"}]
    assert validate_evidence("FEES", "كم رسم التقديم؟", chunks, sources, "2026-10-14")["status"] == "CONFLICTING_EVIDENCE"


def test_planted_conflict_set():
    result = evaluate_planted(load_planted(ROOT / "evaluation" / "conflicts" / "planted.jsonl"))
    assert result["cases"] == 20
    assert result["detection_rate"] == 1.0 and result["false_positive_rate"] == 0.0
    assert result["all_checks_passed"] == 1.0, [r["id"] for r in result["results"] if not r["passed"]]


def test_known_real_conflict_criminology_duration():
    path = ROOT / "data" / "processed" / "chunks.jsonl"
    if not path.exists():
        pytest.skip("run 'python cli.py ingest' first")
    chunks = {json.loads(l)["chunk_id"]: json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l}
    sources = {s["source_id"]: s for s in json.loads((ROOT / "data" / "sources.json").read_text(encoding="utf-8"))}
    report = validate_evidence("STUDY_DURATION", "كم مدة ماجستير علم الجريمة؟",
                               [chunks["PROGRAMS-GUIDE-1448#030"], chunks["FAQ-NAUSS#004"]], sources, "2026-10-14")
    assert len(report["conflicts"]) == 1
    assert report["conflicts"][0]["winner"] == "PROGRAMS-GUIDE-1448"
    assert report["overridden_chunks"] == ["FAQ-NAUSS#004"]
