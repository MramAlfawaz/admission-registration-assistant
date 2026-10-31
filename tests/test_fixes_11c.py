"""Step 11c: safety gaps and regressions found on the held-out set after step 11b.

These fixes were informed by the held-out results, so held-out runs after this step are
reported as optimistic (docs/evaluation.md).
"""
import requests

from app.pipeline.evaluate import run_set, score_row, summarize
from app.rules.selection import rules_for
from tests.test_fixes_11b import HB15, SILENT
from tests.test_generation import CAL6, HB10, HB16, FakeClient, assistant


def test_deadline_with_no_calendar_in_force_is_never_answered():
    obey = {"answer": "لا يزال بإمكان الطالب الاعتذار عن الفصل الأول.", "used_evidence": ["E1"]}
    r = assistant("SEMESTER_WITHDRAWAL", [HB10], obey).answer("هل لا يزال بإمكاني الاعتذار عن الفصل الأول؟", "2025-10-15")
    assert r["status"] == "INSUFFICIENT_EVIDENCE" and r["_trace"]["no_calendar"] == ["RULE-CAL-01"]


def test_decision_request_escalated_even_when_nothing_is_confirmed():
    r = assistant("ADMISSION_PROCEDURE", [HB15], SILENT).answer("Can you grant me an exception to register late?", "2026-10-14")
    assert r["status"] == "STAFF_REVIEW_REQUIRED"


def test_stated_attendance_triggers_its_rule_under_any_intent():
    r = assistant("GRADING_AND_STANDING", [HB16], SILENT).answer("نسبة حضوري 55% وعندي عذر طبي، هل أقدر أدخل النهائي؟", "2026-10-14")
    assert r["status"] == "STAFF_REVIEW_REQUIRED" and r["escalation"]["reason_code"] == "exception_rule"


def test_dialect_deadline_question_keeps_its_rule():
    assert rules_for("POSTPONEMENT", "أبغى أأجل الترم الأول، لحقت ولا لا؟") == ["RULE-CAL-02"]
    assert rules_for("POSTPONEMENT", "كم فصل يمكنني تأجيله خلال الدراسة؟") == []


def test_calendar_row_with_a_year_beats_a_shorter_row():
    r = assistant("ACADEMIC_CALENDAR", [HB15], SILENT).answer("On what date do classes of the 1449 academic year begin?", "2027-03-01")
    assert "2027-08-22" in r["answer"] and "2027-01-03" not in r["answer"]


def test_model_timeout_falls_back_to_rule_sentences():
    a = assistant("SEMESTER_WITHDRAWAL", [CAL6, HB10], error=requests.exceptions.ReadTimeout("slow"))
    r = a.answer("متى آخر موعد للاعتذار عن الفصل الدراسي الأول؟", "2026-10-14")
    assert r["status"] == "ANSWERABLE" and "2026-11-19" in r["answer"]
    assert r["_trace"]["verification_issues"] == ["model unavailable: ReadTimeout"]


def test_evaluation_records_a_crash_and_continues():
    class Broken:
        escalation_log = None

        def answer(self, *a, **k):
            raise requests.exceptions.ReadTimeout("slow")
    items = [{"id": "X1", "question": "q", "language": "ar", "as_of": "2026-10-14", "expected_status": "ANSWERABLE",
              "must_contain": [["x"]], "must_not_contain": []}]
    rows = [score_row(r, {}) for r in run_set(Broken(), items, {})]
    assert rows[0]["response"]["status"] == "ERROR" and rows[0]["correct"] is False
    assert summarize(rows)["overall"]["false_refusal_rate"] == 1.0


# ---- Experiment 4 scoring ----
from app.pipeline.baseline import NoRetrievalModel, is_refusal, score_condition_a, summarize_condition  # noqa: E402
from tests.test_generation import PROMPTS  # noqa: E402

PASSAGES = [{"chunk_id": "HANDBOOK-1446#016", "text": HB16["text"], "tokens": set(__import__("app.retrieval.tokenize", fromlist=["tokenize"]).tokenize(HB16["text"]))}]


def test_condition_a_scoring():
    item = {"id": "X", "language": "ar", "expected_status": "ANSWERABLE", "question": "q",
            "must_contain": [["75"]], "must_not_contain": []}
    good = score_condition_a(item, "يحرم الطالب من دخول الاختبار النهائي إذا قلت نسبة حضوره عن 75%.", PASSAGES)
    bad = score_condition_a(item, "يجب أن تكون نسبة الحضور 90% على الأقل.", PASSAGES)
    assert good["correct"] and good["claims"][0]["label"] == "grounded"
    assert bad["wrong_answer_shown"] and bad["claims"][0]["label"] == "unsupported"
    non = dict(item, expected_status="OUT_OF_SCOPE", must_contain=[])
    assert score_condition_a(non, "Please contact the Deanship.", PASSAGES)["correct"]
    s = summarize_condition([good, bad])["overall"]
    assert s["wrong_answers_shown"] == 1 and s["unsupported_claim_rate"] == 0.5


def test_no_retrieval_model_uses_its_own_prompt():
    client = FakeClient({"answer": "نعم"})
    assert NoRetrievalModel(client, prompts_dir=PROMPTS).answer("سؤال", "ar", "2026-10-14") == "نعم"
    assert "Evidence" not in client.prompts[0] and "سؤال" in client.prompts[0]
    assert is_refusal("I don't know.") and not is_refusal("The fee is 100 riyals.")
