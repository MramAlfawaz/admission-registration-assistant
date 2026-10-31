"""Public demo (step 13d): a slow model must not freeze the page or queue the same question again.

Seen on the Hugging Face Space: a question timed out after 600 s, was retried twice more, and a
second click queued a second question behind it; nothing on the page showed it was working.
"""
from pathlib import Path

import requests

from app.intent.llm_classifier import LLMIntentClassifier
from app.models import llm_client
from app.models.llm_client import HttpTransport
from tests.test_app import ANSWER, FakeAssistant, client_with

PROMPTS = Path(__file__).resolve().parent.parent / "prompts"


def _count_calls(monkeypatch, error):
    calls = []

    def fake_request(*args, **kwargs):
        calls.append(1)
        raise error
    monkeypatch.setattr(llm_client.requests, "request", fake_request)
    monkeypatch.setattr(llm_client.time, "sleep", lambda s: None)
    return calls


class _Patch:
    """Minimal stand-in for pytest's monkeypatch, so these tests need no fixture."""

    def __init__(self):
        self.undo = []

    def setattr(self, obj, name, value):
        self.undo.append((obj, name, getattr(obj, name)))
        setattr(obj, name, value)

    def restore(self):
        for obj, name, value in reversed(self.undo):
            setattr(obj, name, value)


def test_timed_out_generation_is_not_retried():
    patch = _Patch()
    try:
        calls = _count_calls(patch, requests.Timeout("read timed out"))
        try:
            HttpTransport(timeout=1, retries=3).post("http://x/api/generate", {})
        except requests.Timeout:
            pass
        assert len(calls) == 1
    finally:
        patch.restore()


def test_unreachable_model_is_still_retried():
    patch = _Patch()
    try:
        calls = _count_calls(patch, requests.ConnectionError("refused"))
        try:
            HttpTransport(timeout=1, retries=3).post("http://x/api/generate", {})
        except requests.ConnectionError:
            pass
        assert len(calls) == 3
    finally:
        patch.restore()


class _SlowClient:
    def generate_json(self, prompt):
        raise requests.Timeout("read timed out")


def test_intent_falls_back_to_keywords_only_when_given_a_fallback():
    c = LLMIntentClassifier(_SlowClient(), prompts_dir=PROMPTS, fallback=lambda q: "ATTENDANCE")
    assert c.classify("كم نسبة الحضور المطلوبة؟") == "ATTENDANCE" and c.last_source == "keyword fallback"
    strict = LLMIntentClassifier(_SlowClient(), prompts_dir=PROMPTS)
    try:
        strict.classify("x")
        raised = False
    except requests.Timeout:
        raised = True
    assert raised  # evaluation commands get the error, never a silent substitute


def test_page_shows_progress_and_blocks_a_second_submit():
    html = client_with(FakeAssistant(ANSWER)).get("/").get_data(as_text=True)
    assert 'id="busy-note"' in html and "جارٍ البحث" in html and 'data-busy=' in html
    assert "form.dataset.sent" in html and "event.preventDefault()" in html
    html_en = client_with(FakeAssistant(ANSWER)).get("/?lang=en").get_data(as_text=True)
    assert "Searching" in html_en


def test_question_text_is_never_logged():
    import logging
    records = []

    class Keep(logging.Handler):
        def emit(self, record):
            records.append(record.getMessage())
    handler = Keep()
    logger = logging.getLogger("app.routes")
    level = logger.level
    logger.setLevel(logging.INFO)  # pytest keeps the root logger at WARNING
    logger.addHandler(handler)
    try:
        client_with(FakeAssistant(ANSWER)).post("/ask", data={"question": "سؤال خاص جدا", "as_of": "2026-10-14"})
    finally:
        logger.removeHandler(handler)
        logger.setLevel(level)
    assert any("question received" in r for r in records)
    assert not any("سؤال خاص جدا" in r for r in records)
