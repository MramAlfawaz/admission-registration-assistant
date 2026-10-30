from app.documents.chunker import chunk_calendar, chunk_faq, chunk_text

SOURCE = {"source_id": "DOC-1", "title": "t", "document_type": "regulation",
          "authority_level": 1, "version": "1", "effective_from": "2026-01-01",
          "effective_to": None, "language": "ar", "status": "approved"}


def test_chunks_carry_metadata_and_page():
    pages = ["الاعتذار عن الدراسة\n\n" + "كلمة " * 200, "كلمة " * 50]
    chunks = chunk_text(pages, SOURCE)
    first = chunks[0]
    assert first["source_id"] == "DOC-1" and first["version"] == "1"
    assert first["effective_from"] == "2026-01-01" and first["page"] == 1
    assert first["section"] == "الاعتذار عن الدراسة"


def test_chunking_is_deterministic():
    pages = ["فقرة أولى\n\n" + "نص " * 300]
    assert chunk_text(pages, SOURCE) == chunk_text(pages, SOURCE)


def test_article_number_detected():
    chunks = chunk_text(["المادة (24)\n\nيجوز للطالب الاعتذار"], SOURCE)
    assert chunks[0]["article"] == "24"


def test_faq_one_chunk_per_question():
    text = "مقدمة\nهل يوجد سكن؟\nنعم يوجد.\nهل يوجد تأجيل؟\nلا يوجد."
    chunks = chunk_faq([text], SOURCE)
    assert len(chunks) == 2
    assert chunks[1]["text"] == "هل يوجد تأجيل؟\nلا يوجد."


def test_calendar_chunk_text():
    event = {"row": 6, "event": "آخر موعد للاعتذار عن الفصل الدراسي الأول", "day": "الخميس",
             "date_start": "2026-11-19", "date_end": "2026-11-19",
             "hijri_start": "1448-06-09", "hijri_end": "1448-06-09",
             "section": "row 6", "code": "SEMESTER_WITHDRAWAL_DEADLINE", "term_id": "1448-T1"}
    chunk = chunk_calendar([event], SOURCE)[0]
    assert chunk["chunk_id"] == "DOC-1#006"
    assert "2026-11-19" in chunk["text"] and chunk["term_id"] == "1448-T1"
