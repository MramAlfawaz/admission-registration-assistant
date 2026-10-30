import json
import tempfile
from pathlib import Path

from app.documents.calendar_parser import parse_calendar
from app.generation.answer_generator import AnswerGenerator, non_answer
from app.generation.rule_sentences import rule_sentence
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
        "text": "يتقدم بطلب اعتذار عن مواصلة الدراسة إلى رئيس القسم المعني قبل بداية الاختبارات النهائية بأسبوعين. "
                "توصية مجلس القسم وموافقة مجلس الكلية."}
HB16 = {"chunk_id": "HANDBOOK-1446#016", "source_id": "HANDBOOK-1446", "page": 23, "section": "الحرمان",
        "text": "يحرم الطالب من دخول الاختبار النهائي إذا قلت نسبة حضوره عن 75% من المحاضرات والدروس العملية."}
G17 = {"chunk_id": "PROGRAMS-GUIDE-1448#017", "source_id": "PROGRAMS-GUIDE-1448", "page": 33, "section": "شروط القبول الخاصة",
       "text": "الحصول على درجة البكالوريوس في القانون أو العلوم الأمنية، أو أن تكون له خبرة عملية لا تقل عن ثلاث سنوات "
               "في أحد مجالات إنفاذ القانون للحاصلين على البكالوريوس في التخصصات الأخرى."}


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
        self.chunks, self.calls, self.queries = chunks, 0, []

    def search(self, question, as_of, method, k):
        self.calls += 1
        self.queries.append(question)
        return self.chunks[:k]


def assistant(intent, chunks, output=None, error=None, log=None):
    g = AnswerGenerator(FakeClient(output, error), prompts_dir=PROMPTS)
    return Assistant(FixedClassifier(intent), FixedRetriever(chunks), ENGINE, g, BY_ID, escalation_log=log)


def test_every_non_answer_status_is_schema_valid_in_both_languages():
    for status in ("CLARIFICATION_REQUIRED", "INSUFFICIENT_EVIDENCE", "CONFLICTING_EVIDENCE", "OUT_OF_SCOPE"):
        for lang in ("ar", "en"):
            r = non_answer(status, "X", lang, "2026-10-14")
            assert validate_response(r) == [], (status, lang)
            assert r["status"] in STATUSES and r["date_basis"]


def test_clarification_offers_options():
    r = non_answer("CLARIFICATION_REQUIRED", "X", "en", "2026-10-14", missing=["withdrawal_scope"])
    assert [o["value"] for o in r["clarification"]["options"]] == ["course", "semester", "program"]


def test_schema_rejects_answer_without_sources():
    r = non_answer("INSUFFICIENT_EVIDENCE", "X", "ar", "2026-10-14")
    r["status"] = "ANSWERABLE"
    assert "ANSWERABLE responses must cite at least one source" in validate_response(r)


def test_inputs_read_only_when_written():
    assert extract_inputs("نسبة حضوري 70% هل أنحرم؟", {"values": {}})["attendance_percent"] == 70.0
    assert extract_inputs("my GPA is 3.5, do I get a warning?", {"values": {"degree": "master"}})["gpa"] == 3.5
    assert "attendance_percent" not in extract_inputs("هل أنحرم من الاختبار؟", {"values": {}})


def test_rule_sentence_uses_calendar_weekday_and_states_closed():
    result = ENGINE.run("RULE-CAL-01", "2026-12-01")
    en = rule_sentence(result, "en")
    assert "Thursday 2026-11-19" in en and "has closed" in en
    assert "انتهت" in rule_sentence(result, "ar")


def test_prompt_texts_not_in_code():
    for name in ("answer_v2", "classify_intent_v1"):
        _, body = load_prompt(name, PROMPTS)
        for path in (ROOT / "app").rglob("*.py"):
            assert body.splitlines()[0] not in path.read_text(encoding="utf-8"), (name, path)


# ---- regressions from real runs on 2026-10-31 ----

def test_regression_closed_window_with_wrong_weekday_and_advice():
    bad = {"answer": "The deadline is on Friday, 2026-11-19. Students must submit a request before final exams.",
           "used_evidence": ["E1"]}
    r = assistant("SEMESTER_WITHDRAWAL", [CAL6, HB10], bad).answer("When is the semester withdrawal deadline?", "2026-12-01")
    assert r["status"] == "ANSWERABLE" and r["_trace"]["mode"] == "extractive"
    assert "has closed" in r["answer"] and "Friday" not in r["answer"]
    assert any("weekday" in i for i in r["_trace"]["verification_issues"])


def test_regression_ambiguous_withdrawal_asks_even_if_misclassified():
    r = assistant("SEMESTER_WITHDRAWAL", [CAL6, HB10], {"answer": "x"}).answer("هل أقدر أنسحب؟", "2026-10-14")
    assert r["status"] == "CLARIFICATION_REQUIRED" and r["clarification"]["missing"] == "withdrawal_scope"


def test_regression_no_info_claim_and_foreign_script_fall_back_to_quote():
    bad = {"answer": "لا يوجد في النص أي معلومات تؤكد ا需要 ماجستير إنفاذ القانون خبرة عملية.", "used_evidence": ["E1"]}
    r = assistant("ADMISSION_REQUIREMENTS", [G17], bad).answer("هل يحتاج ماجستير إنفاذ القانون خبرة عملية؟", "2026-10-14")
    assert r["_trace"]["mode"] == "extractive" and "ثلاث سنوات" in r["answer"] and "需" not in r["answer"]


def test_regression_misclassified_warning_question_is_not_interrupted():
    r = assistant("GRADUATION_REQUIREMENTS", [HB10], {"answer": "x"}).answer(
        "What happens after two consecutive academic warnings?", "2026-10-14")
    assert r["status"] != "CLARIFICATION_REQUIRED"


# ---- clarification, generation and escalation paths ----

def test_clarification_reply_is_used():
    good = {"answer": "يقدم الطلب إلى رئيس القسم المعني.", "used_evidence": ["E2"]}
    a = assistant("WITHDRAWAL_UNSPECIFIED", [CAL6, HB10], good)
    r = a.answer("هل أقدر أنسحب؟", "2026-10-14", clarification={"withdrawal_scope": "semester"})
    assert r["intent"] == "SEMESTER_WITHDRAWAL" and r["status"] == "ANSWERABLE"
    assert r["rule_outputs"][0]["output"] == "open"
    assert "الاعتذار عن الفصل الدراسي" in a.retriever.queries[0]


def test_verified_generated_answer_keeps_fixed_sentence_first():
    good = {"answer": "يقدم الطلب إلى رئيس القسم المعني قبل بداية الاختبارات النهائية بأسبوعين.",
            "conditions": ["توصية مجلس القسم وموافقة مجلس الكلية"], "used_evidence": ["E2"]}
    r = assistant("SEMESTER_WITHDRAWAL", [CAL6, HB10], good).answer("متى آخر موعد للاعتذار عن الفصل الدراسي الأول؟", "2026-10-14")
    assert r["_trace"]["mode"] == "generated" and r["verified"] is True and validate_response(r) == []
    assert r["answer"].startswith("آخر موعد للاعتذار عن الفصل الدراسي الأول هو الخميس 2026-11-19")
    assert r["sources"][0]["chunk_id"] == "HANDBOOK-1446#010"


def test_unusable_model_output_falls_back_to_quotes():
    r = assistant("ATTENDANCE", [HB16], error=ValueError("bad json")).answer("كم نسبة الحضور المطلوبة؟", "2026-10-14")
    assert r["status"] == "ANSWERABLE" and r["_trace"]["mode"] == "extractive" and "75%" in r["answer"]


def test_out_of_scope_never_retrieves_and_points_elsewhere():
    a = assistant("OUT_OF_SCOPE", [CAL6])
    r = a.answer("Is there housing?", "2026-10-14")
    assert r["status"] == "OUT_OF_SCOPE" and a.retriever.calls == 0 and "Deanship" not in r["required_action"]


def test_course_withdrawal_has_no_supporting_source():
    assert assistant("COURSE_WITHDRAWAL", [CAL6, HB10]).answer("كيف أحذف مادة؟", "2026-10-14")["status"] == "INSUFFICIENT_EVIDENCE"


def test_exception_rule_escalates_with_confirmed_facts():
    good = {"answer": "يحرم الطالب إذا قلت نسبة حضوره عن 75%.", "used_evidence": ["E1"]}
    log = Path(tempfile.mkdtemp()) / "esc.jsonl"
    r = assistant("ATTENDANCE", [HB16], good, log=str(log)).answer("نسبة حضوري 70% هل أنحرم من الاختبار؟", "2026-10-14")
    assert r["status"] == "STAFF_REVIEW_REQUIRED" and validate_response(r) == []
    assert r["escalation"]["reason_code"] == "exception_rule" and r["escalation"]["confirmed"]
    record = json.loads(log.read_text(encoding="utf-8").splitlines()[0])
    assert record["reason"] == "exception_rule" and "question" not in record


def test_decision_request_escalates():
    r = assistant("ATTENDANCE", [HB16], {"answer": "يحرم الطالب إذا قلت نسبة حضوره عن 75%.", "used_evidence": ["E1"]}).answer(
        "أطلب استثناء من شرط الحضور", "2026-10-14")
    assert r["status"] == "STAFF_REVIEW_REQUIRED" and r["escalation"]["next_step"]
