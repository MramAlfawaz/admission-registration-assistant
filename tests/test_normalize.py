from app.documents.normalize import clean_text, normalize_for_search


def test_removes_tatweel():
    assert clean_text("البنـــــد") == "البند"


def test_unifies_presentation_forms():
    assert clean_text("آﺧﺮ") == "آخر"


def test_removes_zero_width():
    assert clean_text("\u200bنعم\u200b") == "نعم"


def test_correct_text_unchanged():
    good = "نظام الدراسة والاختبارات الأكاديمية"
    assert clean_text(good) == good


def test_search_form_matches_variants():
    assert normalize_for_search("الإختبارات النهائية") == normalize_for_search("الاختبارات النهائيه")
