from app import create_app
from app.generation.answer_generator import non_answer


class FakeAssistant:
    sources_by_id = {"CALENDAR-1448": {"title": "التقويم الأكاديمي 1448-1449هـ"},
                     "HANDBOOK-1446": {"title": "دليل الطالب 1446هـ"}}

    def __init__(self, response=None, error=None):
        self.response, self.error, self.calls = response, error, []

    def answer(self, question, as_of, clarification=None):
        self.calls.append((question, as_of, clarification))
        if self.error:
            raise self.error
        return self.response


ANSWER = {"status": "ANSWERABLE", "intent": "SEMESTER_WITHDRAWAL", "language": "ar", "as_of": "2026-10-14",
          "answer": "آخر موعد للاعتذار عن الفصل الدراسي الأول هو الخميس 2026-11-19 (1448-06-09هـ).",
          "conditions": ["توصية مجلس القسم وموافقة مجلس الكلية"], "required_action": "",
          "rule_outputs": [], "sources": [{"source_id": "CALENDAR-1448", "section": "row 6"},
                                          {"source_id": "HANDBOOK-1446", "chunk_id": "HANDBOOK-1446#010", "page": 18,
                                           "section": "تأجيل الدراسة"}],
          "date_basis": "بناءً على المعلومات المعتمدة المتاحة بتاريخ 2026-10-14.", "clarification": None,
          "escalation": None, "verified": True, "_trace": {"mode": "generated"}}


def client_with(assistant):
    app = create_app("testing")
    app.extensions["assistant"] = assistant
    return app.test_client()


def test_health():
    client = create_app("testing").test_client()
    r = client.get("/health")
    assert r.status_code == 200
    assert r.get_json()["errors"] == []


def test_page_renders_in_arabic_right_to_left():
    r = client_with(FakeAssistant(ANSWER)).get("/")
    html = r.get_data(as_text=True)
    assert r.status_code == 200 and 'dir="rtl"' in html and "مساعد القبول والتسجيل" in html


def test_answer_shows_status_sources_and_date_basis():
    fake = FakeAssistant(ANSWER)
    html = client_with(fake).post("/ask", data={"question": "متى آخر موعد للاعتذار؟", "as_of": "2026-10-14"}).get_data(as_text=True)
    assert "إجابة من المصادر المعتمدة" in html and "status-answerable" in html
    assert "التقويم الأكاديمي 1448-1449هـ" in html and "صفحة 18" in html
    assert "بناءً على المعلومات المعتمدة المتاحة بتاريخ 2026-10-14" in html
    assert fake.calls == [("متى آخر موعد للاعتذار؟", "2026-10-14", None)]


def test_clarification_offers_buttons_and_passes_the_reply_back():
    r = non_answer("CLARIFICATION_REQUIRED", "WITHDRAWAL_UNSPECIFIED", "ar", "2026-10-14", missing=["withdrawal_scope"])
    fake = FakeAssistant(r)
    client = client_with(fake)
    html = client.post("/ask", data={"question": "هل أقدر أنسحب؟", "as_of": "2026-10-14"}).get_data(as_text=True)
    assert 'name="clarify_withdrawal_scope" value="semester"' in html
    client.post("/ask", data={"question": "هل أقدر أنسحب؟", "as_of": "2026-10-14", "clarify_withdrawal_scope": "semester"})
    assert fake.calls[-1][2] == {"withdrawal_scope": "semester"}


def test_english_answer_is_left_to_right():
    en = dict(ANSWER, language="en", answer="The deadline is Thursday 2026-11-19.", date_basis="Based on approved information available on 2026-10-14.")
    html = client_with(FakeAssistant(en)).post("/ask", data={"question": "When is the deadline?"}).get_data(as_text=True)
    assert 'lang="en" dir="ltr"' in html and "Answer from approved sources" in html


def test_errors_are_readable_not_tracebacks():
    r = client_with(FakeAssistant(error=RuntimeError("ollama down"))).post("/ask", data={"question": "سؤال", "as_of": "2026-10-14"})
    html = r.get_data(as_text=True)
    assert r.status_code == 503 and "تعذر تجهيز الإجابة" in html and "Traceback" not in html and "ollama" not in html
    r = client_with(FakeAssistant(ANSWER)).post("/ask", data={"question": "  "})
    assert r.status_code == 400


def test_api_returns_the_response_without_the_trace():
    r = client_with(FakeAssistant(ANSWER)).post("/api/ask", json={"question": "متى؟", "as_of": "2026-10-14"})
    body = r.get_json()
    assert r.status_code == 200 and body["errors"] == [] and "_trace" not in body["results"][0]
    assert client_with(FakeAssistant(ANSWER)).post("/api/ask", json={"question": "x", "as_of": "14/10/2026"}).status_code == 400
