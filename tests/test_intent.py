import json
from collections import Counter
from pathlib import Path

from app.intent.context_extractor import extract_context
from app.intent.evaluate import evaluate, load_questions
from app.intent.keyword_baseline import classify
from app.intent.language import answer_language, detect_language
from app.intent.taxonomy import INTENTS

QUESTIONS = Path(__file__).resolve().parent.parent / "evaluation" / "intent" / "questions.jsonl"


def test_language_detection():
    assert detect_language("متى آخر موعد للاعتذار؟") == "ar"
    assert detect_language("When is the withdrawal deadline?") == "en"
    assert detect_language("متى الـ final exams للفصل الأول؟") == "mixed"
    assert detect_language("2026") == "ar"


def test_answer_language_follows_majority_script():
    assert answer_language("هل الـ IELTS شرط للقبول؟") == "ar"
    assert answer_language("Is IELTS required for القبول?") == "en"


def test_keyword_baseline_examples():
    assert classify("متى آخر موعد للاعتذار عن الفصل الدراسي الأول؟") == "SEMESTER_WITHDRAWAL"
    assert classify("Can I drop a course?") == "COURSE_WITHDRAWAL"
    assert classify("هل يوجد سكن للطلاب؟") == "OUT_OF_SCOPE"
    assert classify("hello there") == "OUT_OF_SCOPE"


def test_context_is_never_invented():
    result = extract_context("Can I withdraw?", "WITHDRAWAL_UNSPECIFIED")
    assert result["values"] == {} and result["missing"] == ["withdrawal_scope"]


def test_context_values_extracted():
    result = extract_context("أنا طالب ماجستير، متى الاعتذار عن الفصل الثاني؟", "SEMESTER_WITHDRAWAL")
    assert result["values"]["degree_level"] == "master"
    assert result["values"]["term"] == "T2"
    assert result["missing"] == []


def test_missing_degree_for_duration():
    assert extract_context("كم مدة الدراسة؟", "STUDY_DURATION")["missing"] == ["degree_level"]


def test_extractor_matches_labelled_missing_context():
    for r in load_questions(QUESTIONS):
        assert extract_context(r["question"], r["intent"])["missing"] == r["expected_missing"], r["id"]


def test_question_set_integrity():
    rows = load_questions(QUESTIONS)
    assert len({r["id"] for r in rows}) == len(rows)
    assert all(r["intent"] in INTENTS for r in rows)
    assert all(r["origin"] == "synthetic" for r in rows)
    assert all(detect_language(r["question"]) == r["language"] for r in rows)
    assert min(Counter(r["intent"] for r in rows).values()) >= 5
    assert {r["split"] for r in rows} == {"dev", "test"}


def test_perfect_classifier_scores_one():
    rows = load_questions(QUESTIONS, "test")
    gold = {r["question"]: r["intent"] for r in rows}
    result = evaluate(lambda q: gold[q], rows)
    assert result["overall"]["macro_f1"] == 1.0 and result["errors"] == []
