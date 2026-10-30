import json
from pathlib import Path

from app.documents.calendar_parser import parse_calendar
from app.rules.calendar_rules import CalendarStore
from app.rules.rule_engine import RuleEngine

ROOT = Path(__file__).resolve().parent.parent
LIBRARY = json.loads((ROOT / "rules" / "rule_library.json").read_text(encoding="utf-8"))
SOURCES = json.loads((ROOT / "data" / "sources.json").read_text(encoding="utf-8"))
EVENTS = parse_calendar((ROOT / "tests" / "fixtures" / "calendar_1448.txt").read_text(encoding="utf-8"),
                        "CALENDAR-1448", "1448")
ENGINE = RuleEngine(LIBRARY, CalendarStore({"CALENDAR-1448": EVENTS}, SOURCES))


def out(rule_id, as_of, **inputs):
    return ENGINE.run(rule_id, as_of, **inputs)["output"]


# ---- calendar rules: day before, on, and after each boundary ----

def test_cal01_boundaries():
    assert out("RULE-CAL-01", "2026-11-18") == "open"
    assert out("RULE-CAL-01", "2026-11-19") == "open"
    assert out("RULE-CAL-01", "2026-11-20") == "closed"
    assert out("RULE-CAL-01", "2026-11-20", term_id="1448-T2") == "open"
    assert out("RULE-CAL-01", "2027-05-24") == "open"
    assert out("RULE-CAL-01", "2027-05-25") == "closed"
    details = ENGINE.run("RULE-CAL-01", "2026-10-14")["details"]
    assert details["date"] == "2026-11-19" and details["term_id"] == "1448-T1"
    assert details["term_basis"].startswith("current") and details["calendar_row"] == 6


def test_cal_unknown_without_calendar():
    result = ENGINE.run("RULE-CAL-01", "2026-08-01")
    assert result["output"] == "unknown" and "no academic calendar" in result["details"]["reason"]
    assert out("RULE-CAL-01", "2026-10-14", term_id="1448-T3") == "unknown"


def test_cal02_boundaries():
    assert out("RULE-CAL-02", "2026-08-27") == "open"
    assert out("RULE-CAL-02", "2026-08-28") == "closed"
    assert out("RULE-CAL-02", "2027-01-07") == "open"
    assert out("RULE-CAL-02", "2027-01-08") == "closed"


def test_cal03_boundaries():
    assert out("RULE-CAL-03", "2026-08-13") == "open"
    assert out("RULE-CAL-03", "2026-08-14") == "closed"
    assert out("RULE-CAL-03", "2026-12-26") == "open"
    assert out("RULE-CAL-03", "2026-12-27") == "closed"
    assert ENGINE.run("RULE-CAL-03", "2026-12-20")["details"]["term_id"] == "1448-T2"


def test_cal04_boundaries():
    assert out("RULE-CAL-04", "2026-08-22") == "refund_eligible"
    assert out("RULE-CAL-04", "2026-08-23") == "refund_not_eligible"


def test_cal05_boundaries():
    assert out("RULE-CAL-05", "2026-12-05") == "open"
    assert out("RULE-CAL-05", "2026-12-06") == "closed"


# ---- regulation thresholds: on and either side of each limit ----

def test_reg01_boundaries():
    assert out("RULE-REG-01", "2026-10-14", attendance_percent=75) == "eligible_for_final"
    assert out("RULE-REG-01", "2026-10-14", attendance_percent=74.9) == "deprived_exception_possible"
    assert out("RULE-REG-01", "2026-10-14", attendance_percent=50) == "deprived_exception_possible"
    assert out("RULE-REG-01", "2026-10-14", attendance_percent=49.9) == "deprived"


def test_reg02_boundaries():
    assert out("RULE-REG-02", "2026-10-14", course_grade=70) == "passed"
    assert out("RULE-REG-02", "2026-10-14", course_grade=69.99) == "failed"


def test_reg03_boundaries():
    assert out("RULE-REG-03", "2026-10-14", degree="master", gpa=3.75) == "no_warning"
    assert out("RULE-REG-03", "2026-10-14", degree="master", gpa=3.74) == "warning"
    assert out("RULE-REG-03", "2026-10-14", degree="diploma", gpa=3.00) == "no_warning"
    assert out("RULE-REG-03", "2026-10-14", degree="diploma", gpa=2.99) == "warning"
    assert out("RULE-REG-03", "2026-10-14", degree="bachelor", gpa=3.0) == "unknown"


def test_reg04_boundaries():
    assert out("RULE-REG-04", "2026-10-14", consecutive_warnings=1) == "enrolment_continues"
    assert out("RULE-REG-04", "2026-10-14", consecutive_warnings=2) == "enrolment_closed"


def test_reg05_boundaries():
    assert out("RULE-REG-05", "2026-10-14", semesters_since_closure=4, previous_reenrolments=0) == "eligible_to_apply"
    assert out("RULE-REG-05", "2026-10-14", semesters_since_closure=5, previous_reenrolments=0) == "not_eligible"
    assert out("RULE-REG-05", "2026-10-14", semesters_since_closure=1, previous_reenrolments=1) == "exception_only"


def test_reg06_boundaries():
    assert out("RULE-REG-06", "2026-10-14", degree="master", appeals_used=0) == "3"
    assert out("RULE-REG-06", "2026-10-14", degree="diploma", appeals_used=2) == "0"
    assert out("RULE-REG-06", "2026-10-14", degree="phd", appeals_used=5) == "0"


def test_elig01_boundaries():
    assert out("RULE-ELIG-01", "2026-10-14", degree="phd", gpa=3.75) == "meets_gpa"
    assert out("RULE-ELIG-01", "2026-10-14", degree="phd", gpa=3.74) == "below_gpa"
    assert out("RULE-ELIG-01", "2026-10-14", degree="diploma", gpa=3.0) == "meets_gpa"


def test_elig02_boundaries():
    clean = {"failed_any_course": False, "disciplinary_penalty": False, "enrolment_ever_closed": False}
    assert out("RULE-ELIG-02", "2026-10-14", gpa=4.75, **clean) == "first_honours"
    assert out("RULE-ELIG-02", "2026-10-14", gpa=4.74, **clean) == "second_honours"
    assert out("RULE-ELIG-02", "2026-10-14", gpa=4.50, **clean) == "second_honours"
    assert out("RULE-ELIG-02", "2026-10-14", gpa=4.49, **clean) == "no_honours"
    assert out("RULE-ELIG-02", "2026-10-14", gpa=4.9, **{**clean, "failed_any_course": True}) == "not_eligible"


# ---- engine behaviour and library integrity ----

def test_missing_input_is_unknown_never_guessed():
    result = ENGINE.run("RULE-REG-01", "2026-10-14")
    assert result["output"] == "unknown" and "attendance_percent" in result["details"]["reason"]


def test_rule_not_in_force_before_effective_date():
    assert out("RULE-REG-02", "2024-07-31", course_grade=80) == "not_applicable"


def test_every_result_cites_sources():
    for rule in LIBRARY:
        assert ENGINE.run(rule["rule_id"], "2026-10-14")["sources"] == rule["sources"]


def test_library_integrity():
    known = {s["source_id"] for s in SOURCES}
    test_names = (Path(__file__).read_text(encoding="utf-8"))
    ids = [r["rule_id"] for r in LIBRARY]
    assert len(ids) == len(set(ids))
    for r in LIBRARY:
        assert r["sources"] and all(s["source_id"] in known for s in r["sources"]), r["rule_id"]
        assert r["condition"] and r["outputs"] and r["effective_from"], r["rule_id"]
        assert r["tests"] and all(f"def {t}(" in test_names for t in r["tests"]), r["rule_id"]
        if r["kind"] == "calendar":
            assert r["event_code"] and r["comparison"] in ("on_or_before", "before") and r["term_basis"]
        else:
            from app.rules import registration_rules
            assert hasattr(registration_rules, r["function"]), r["rule_id"]
