import json
from pathlib import Path

from app.documents.calendar_parser import parse_calendar
from app.generation.answer_generator import AnswerGenerator, non_answer
from app.models.prompts import load_prompt
from app.pipeline.assistant import Assistant
from app.rules.calendar_rules import CalendarStore
from app.rules.rule_engine import RuleEngine
from app.rules.selection import extract_inputs, run_rules
from app.schemas.answer import STATUSES, validate_response

ROOT = Path(__file__).resolve().parent.parent
PROMPTS = ROOT / "prompts"
SOURCES = json.loads((ROOT / "data" / "sources.json").read_text(encoding="utf-8"))
BY_ID = {s["source_id"]: s for s in SOURCES}
EVENTS = parse_calendar((ROOT / "tests" / "fixtures" / "calendar_1448.txt").read_text(encoding="utf-8"),
                        "CALENDAR-1448", "1448")
ENGINE = RuleEngine(json.loads((ROOT / "rules" / "rule_library.json").read_text(encoding="utf-8")),
                    CalendarStore({"CALENDAR-1448": EVENTS}, SOURCES))
CAL6 = {"chunk_id": "CALENDAR-1448#006", "source_id": "CALENDAR-1448", "page": 1, "section": "row 6",
        "text": "آخر موعد للاعتذار عن الفصل الدراسي الأول: الخميس 2026-11-19م (1448-06-09هـ)"}
HB10 = {"chunk_id": "HANDBOOK-1446#010", "source_id": "HANDBOOK-1446", "page": 18, "section": "الاعتذار عن الدراسة",
        "text": "يتقدم بطلب اعتذار عن مواصلة الدراسة إلى رئيس القسم المعني قبل بداية الاختبارات النهائية بأسبوعين."}


class FakeClient:
    def __init__(self, output=None, error=None):
        self.output, self.error, self.prompts = output, error, []

    def generate_json(self, prompt):
        self.prompts.append(prompt)
        if self.error:
            raise self.error
        return self.output


class FixedClassifier:
    def __init__(self, intent):
        self.intent = intent

    def classify(self, question):
        return self.intent


class FixedRetriever:
    def __init__(self, chunks):
        self.chunks, self.calls = chunks, 0

    def search(self, question, as_of, method, k):
        self.calls += 1
        return self.chunks[:k]


def generator(output=None, error=None):
    return AnswerGenerator(FakeClient(output, error), prompts_dir=PROMPTS)


def test_every_non_answer_status_is_schema_valid_in_both_languages():
    for status in ("CLARIFICATION_REQUIRED", "INSUFFICIENT_EVIDENCE", "CONFLICTING_EVIDENCE", "OUT_OF_SCOPE"):
        for lang in ("ar", "en"):
            r = non_answer(status, "X", lang, "2026-10-14")
            assert validate_response(r) == [], (status, lang)
            assert r["status"] in STATUSES and r["date_basis"]


def test_clarification_asks_one_specific_question():
    r = non_answer("CLARIFICATION_REQUIRED", "WITHDRAWAL_UNSPECIFIED", "en", "2026-10-14", missing=["withdrawal_scope"])
    assert r["clarification"]["missing"] == "withdrawal_scope" and "course" in r["answer"]


def test_schema_rejects_answer_without_sources():
    r = non_answer("INSUFFICIENT_EVIDENCE", "X", "ar", "2026-10-14")
    r["status"] = "ANSWERABLE"
    assert "ANSWERABLE responses must cite at least one source" in validate_response(r)


def test_inputs_read_only_when_written():
    assert extract_inputs("نسبة حضوري 70% هل أنحرم؟", {"values": {}})["attendance_percent"] == 70.0
    assert extract_inputs("my GPA is 3.5, do I get a warning?", {"values": {"degree": "master"}})["gpa"] == 3.5
    empty = extract_inputs("هل أنحرم من الاختبار؟", {"values": {}})
    assert "attendance_percent" not in empty and "gpa" not in empty


def test_rules_needing_student_values_are_skipped():
    assert run_rules(ENGINE, "ATTENDANCE", "كم نسبة الحضور؟", {"values": {}}, "2026-10-14") == []
    results = run_rules(ENGINE, "SEMESTER_WITHDRAWAL", "متى آخر موعد للاعتذار؟", {"values": {}}, "2026-10-14")
    assert [(r["rule_id"], r["output"]) for r in results] == [("RULE-CAL-01", "open")]


def test_answer_cites_used_evidence_and_rule_sources():
    g = generator({"answer": "آخر موعد للاعتذار هو 2026-11-19.", "conditions": ["قبل الاختبارات بأسبوعين"],
                   "required_action": "قدّم الطلب لرئيس القسم.", "used_evidence": ["E1"]})
    rules = run_rules(ENGINE, "SEMESTER_WITHDRAWAL", "متى آخر موعد للاعتذار؟", {"values": {}}, "2026-10-14")
    r = g.answer("متى آخر موعد للاعتذار؟", "SEMESTER_WITHDRAWAL", "ar", "2026-10-14", [CAL6, HB10], rules, [])
    assert validate_response(r) == []
    assert r["sources"][0]["chunk_id"] == "CALENDAR-1448#006"
    assert {"source_id": "HANDBOOK-1446", "section": "p18 الاعتذار عن الدراسة"} in r["sources"]
    prompt = g.client.prompts[0]
    assert "[E1] CALENDAR-1448" in prompt and "RULE-CAL-01: result = open, date 2026-11-19" in prompt
    assert "{{" not in prompt


def test_unknown_evidence_labels_fall_back_to_all_given():
    g = generator({"answer": "text", "used_evidence": ["E9"]})
    r = g.answer("q", "SEMESTER_WITHDRAWAL", "en", "2026-10-14", [CAL6, HB10], [], [])
    assert [s["chunk_id"] for s in r["sources"]] == ["CALENDAR-1448#006", "HANDBOOK-1446#010"]


def test_empty_or_invalid_model_output_becomes_insufficient():
    assert generator({"answer": ""}).answer("q", "X", "en", "2026-10-14", [CAL6], [], [])["status"] == "INSUFFICIENT_EVIDENCE"
    assert generator(error=ValueError("bad")).answer("q", "X", "en", "2026-10-14", [CAL6], [], [])["status"] == "INSUFFICIENT_EVIDENCE"


def test_answer_prompt_text_not_in_code():
    _, body = load_prompt("answer_v1", PROMPTS)
    for path in (ROOT / "app").rglob("*.py"):
        assert body.splitlines()[0] not in path.read_text(encoding="utf-8"), path


def test_pipeline_out_of_scope_never_retrieves():
    retriever = FixedRetriever([CAL6])
    a = Assistant(FixedClassifier("OUT_OF_SCOPE"), retriever, ENGINE, generator({"answer": "x"}), BY_ID)
    assert a.answer("Is there housing?", "2026-10-14")["status"] == "OUT_OF_SCOPE" and retriever.calls == 0


def test_pipeline_asks_for_clarification():
    a = Assistant(FixedClassifier("WITHDRAWAL_UNSPECIFIED"), FixedRetriever([CAL6]), ENGINE, generator(), BY_ID)
    r = a.answer("Can I withdraw?", "2026-10-14")
    assert r["status"] == "CLARIFICATION_REQUIRED" and r["language"] == "en"


def test_pipeline_course_withdrawal_has_no_supporting_source():
    a = Assistant(FixedClassifier("COURSE_WITHDRAWAL"), FixedRetriever([CAL6, HB10]), ENGINE, generator(), BY_ID)
    assert a.answer("اقدر اسحب المادة؟", "2026-10-14")["status"] == "INSUFFICIENT_EVIDENCE"


def test_pipeline_full_answer():
    g = generator({"answer": "The deadline is 2026-11-19.", "conditions": [], "required_action": "Apply to the head of department.",
                   "used_evidence": ["E1", "E2"]})
    a = Assistant(FixedClassifier("SEMESTER_WITHDRAWAL"), FixedRetriever([CAL6, HB10]), ENGINE, g, BY_ID)
    r = a.answer("When is the semester withdrawal deadline?", "2026-10-14")
    assert r["status"] == "ANSWERABLE" and validate_response(r) == []
    assert r["rule_outputs"][0]["output"] == "open" and r["_trace"]["evidence_status"] == "OK"
