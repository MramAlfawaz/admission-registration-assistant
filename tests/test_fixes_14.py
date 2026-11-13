"""Fix after the final demo check (2026-11-13): the Deanship's name is not evidence about registration."""
from app.generation.extractive import evidence_fits, relevance_filter

REFUND = ("لا يحق للطالب المعتذر استعادة الرسوم الدراسية المدفوعة الانسحاب من الجامعة أولاً: "
          "يجوز للطالب تقديم طلب الانسحاب من البرنامج الأكاديمي إلى عمادة القبول والتسجيل")


def test_office_name_alone_does_not_fit_a_registration_question():
    question = "ماهو موعد التسجيل للفصل القادم؟"
    assert not evidence_fits(question, [REFUND])
    assert not relevance_filter(question)(REFUND)


def test_registration_in_the_text_still_fits():
    question = "ماهو موعد التسجيل للفصل القادم؟"
    text = "يحجب التسجيل عن الطالب في حال عدم التزامه بسداد الرسوم الدراسية للفصل القادم"
    assert evidence_fits(question, [text])


def test_question_naming_the_office_keeps_the_name():
    question = "ما البريد الإلكتروني لعمادة القبول والتسجيل؟"
    text = "للتواصل مع عمادة القبول والتسجيل: admission@nauss.edu.sa"
    assert evidence_fits(question, [text])
