"""User feedback (step 13e): "the sources give only the document name"; each title now links to the document."""
from app.routes import _source_view
from tests.test_app import ANSWER, FakeAssistant, client_with


class _A:
    sources_by_id = {"HANDBOOK-1446": {"title": "دليل الطالب 1446هـ",
                                       "url": "https://nauss.edu.sa/ar/eservices/Documents/Student-Handbook%20(1).pdf"},
                     "FAQ-NAUSS": {"title": "الأسئلة الشائعة", "url": "https://nauss.edu.sa/ar/Pages/faqs.aspx"},
                     "NO-URL": {"title": "بدون رابط"}}


def test_pdf_source_links_to_the_first_cited_page():
    view = _source_view(_A(), [{"source_id": "HANDBOOK-1446", "page": 23, "section": "الحرمان"},
                               {"source_id": "HANDBOOK-1446", "page": 18, "section": "الاعتذار"}], "ar")
    assert view[0]["url"].endswith("Student-Handbook%20(1).pdf#page=23")


def test_web_page_and_missing_url():
    view = _source_view(_A(), [{"source_id": "FAQ-NAUSS", "page": 1}, {"source_id": "NO-URL"}], "ar")
    assert view[0]["url"] == "https://nauss.edu.sa/ar/Pages/faqs.aspx" and view[1]["url"] is None


def test_page_renders_source_links_opening_in_a_new_tab():
    assistant = FakeAssistant(ANSWER)
    assistant.sources_by_id = {**assistant.sources_by_id,
                               "CALENDAR-1448": {"title": "التقويم الأكاديمي 1448-1449هـ",
                                                 "url": "https://nauss.edu.sa/ar/academic-programmes/Documents/AcademicCalendar.pdf"}}
    html = client_with(assistant).post("/ask", data={"question": "متى آخر موعد للاعتذار؟", "as_of": "2026-10-14"}).get_data(as_text=True)
    assert 'href="https://nauss.edu.sa/ar/academic-programmes/Documents/AcademicCalendar.pdf"' in html
    assert 'target="_blank" rel="noopener"' in html
