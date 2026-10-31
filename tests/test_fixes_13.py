"""Step 13: fixes from testing the student page by hand (step 12).

1. An escalated answer showed a model sentence as "what can be confirmed", and it implied the
   student met the conditions. Confirmed text is now only rule sentences and quotes.
2. Sentences saying a condition is met are dropped unless they are conditional ("if you meet...").
3. The same document was listed once per passage; the page now shows one line per document.
4. A quote about the second term answered a question about the first.
"""
from app.generation.extractive import mentions_other_term
from app.routes import _source_view
from app.safety.verifier import verify_text
from tests.test_generation import HB16, assistant

HB_TERMS = {"chunk_id": "HANDBOOK-1446#030", "source_id": "HANDBOOK-1446", "page": 30, "section": "التسجيل",
            "text": "يبدأ تسجيل المقررات للفصل الدراسي الثاني قبل بداية الدراسة بأسبوعين عبر البوابة الإلكترونية. "
                    "يبدأ تسجيل المقررات للفصل الدراسي الأول قبل بداية الدراسة بأسبوع واحد عبر البوابة الإلكترونية."}


def test_escalation_confirms_only_rule_sentences_and_quotes():
    model = {"answer": "يحرم الطالب إذا قلت نسبة حضوره عن 75%.", "used_evidence": ["E1"]}
    r = assistant("ATTENDANCE", [HB16], model).answer("نسبة حضوري 70% هل أنحرم من الاختبار؟", "2026-10-14")
    assert r["status"] == "STAFF_REVIEW_REQUIRED"
    confirmed = r["escalation"]["confirmed"]
    assert confirmed and model["answer"] not in confirmed
    rule_texts = r["_trace"]["rule_texts"]
    assert all(c in rule_texts or c.startswith("«") for c in confirmed)


def test_escalation_sources_follow_what_is_confirmed():
    r = assistant("ATTENDANCE", [HB16], {"answer": "x", "used_evidence": []}).answer("نسبة حضوري 70% هل أنحرم من الاختبار؟", "2026-10-14")
    ids = {s["source_id"] for s in r["sources"]}
    assert ids and ids <= {"HANDBOOK-1446"}


def test_sentence_saying_conditions_are_met_is_dropped():
    for text, lang in [("لقد استوفيت جميع الشروط المطلوبة للقبول.", "ar"),
                       ("بما أنك تستوفي جميع الشروط يمكنك التسجيل.", "ar"),
                       ("You have met all the requirements for the programme.", "en"),
                       ("You are eligible to register for the course.", "en")]:
        assert "states or implies an official decision" in verify_text(text, lang, [text], [])


def test_conditional_sentence_about_conditions_is_kept():
    for text, lang in [("إذا كنت تستوفي جميع الشروط يمكنك التقديم عبر البوابة.", "ar"),
                       ("If you meet the requirements, apply through the portal.", "en")]:
        assert "states or implies an official decision" not in verify_text(text, lang, [text], [])


def test_sources_grouped_one_line_per_document():
    class A:
        sources_by_id = {"HANDBOOK-1446": {"title": "دليل الطالب"}, "CALENDAR-1448": {"title": "التقويم"}}
    sources = [{"source_id": "HANDBOOK-1446", "page": 18, "section": "الاعتذار"},
               {"source_id": "CALENDAR-1448", "section": "row 6"},
               {"source_id": "HANDBOOK-1446", "page": 23, "section": "الحرمان"},
               {"source_id": "HANDBOOK-1446", "page": 18, "section": "الاعتذار"}]
    view = _source_view(A(), sources, "ar")
    assert [v["id"] for v in view] == ["HANDBOOK-1446", "CALENDAR-1448"]
    assert view[0]["where"].count("صفحة") == 2 and "، " in view[0]["where"]
    assert view[1]["where"] == "الصف 6 في التقويم"


def test_other_term_detected_in_both_languages():
    assert mentions_other_term("آخر موعد للاعتذار عن الفصل الدراسي الثاني", "T1")
    assert not mentions_other_term("آخر موعد للاعتذار عن الفصل الدراسي الثاني", "T2")
    assert mentions_other_term("Second semester classes begin on 3 January.", "T1")
    assert not mentions_other_term("الفصل الأول والفصل الثاني", "T1")
    assert mentions_other_term("يبدأ التسجيل للفصل الدراسي الثاني", "T1")
    assert not mentions_other_term("any sentence", None)


def test_quote_about_the_other_term_is_not_used():
    a = assistant("ADMISSION_PROCEDURE", [HB_TERMS])
    question = "متى يبدأ تسجيل المقررات للفصل الدراسي الأول؟"
    quotes = [q for q, _ in a._quotes(question, [HB_TERMS], [], "T1")]
    assert quotes and all("الثاني" not in q for q in quotes)


# ---- step 13b: review of the escalations in holdout_v3 and e2e_v3 ----

from app.generation.extractive import readable  # noqa: E402

HB_TABLE = {"chunk_id": "HANDBOOK-1446#025", "source_id": "HANDBOOK-1446", "page": 25, "section": "التقديرات",
            "text": "00ح محروم معادلة-مع معادلة الدرجات والتقديرات 25 Value Grade Points Mark Exceptional A+ 5. "
                    "يحصل الطالب على تقدير ممتاز مرتفع إذا كانت درجته في المقرر من خمس وتسعين إلى مائة."}


def test_damaged_extraction_text_is_not_readable():
    # Real sentences from the v3 escalations (H031, H033, E081, E083).
    assert not readable("يحرم الطالب من دخول الاختبار النهائي إذا قلت نسبة حضوره عن 1 ) من المحاضرات الفصل75%( الدراسي")
    assert not readable("00ح محروم معادلة-مع معادلة الدرجات والتقديرات 25 Value Grade Points Mark")
    assert not readable("وفكرية، وغيرها ماجستير الأمن الوطني48 ماجستير الأمن الوطني أهداف البرنامج")
    assert not readable("75( ) وأقل من4:50( الحاصل على معدل تراكمي أعلى من أو يساوي ) عند التخرج")


def test_clean_text_is_readable():
    assert readable("بداية الاختبارات النهائية للفصل الدراسي الأول: الأحد 2026-12-06م (1448-06-26هـ)")
    assert readable("يتم التواصل مع عمادة القبول والتسجيل عبر البريد admission@nauss.edu.sa في أوقات الدوام")
    assert readable("Final exams for the first semester begin on Sunday (6 December 2026).")


def test_personal_record_escalation_shows_no_quotes():
    r = assistant("GRADING_AND_STANDING", [HB_TABLE], {"answer": "حصلت على تقدير جيد.", "used_evidence": ["E1"]}).answer(
        "وش درجاتي في الترم الماضي؟", "2026-10-14")
    assert r["status"] == "STAFF_REVIEW_REQUIRED" and r["escalation"]["reason_code"] == "personal_record"
    assert not any(c.startswith("«") for c in r["escalation"]["confirmed"])
    assert "حصلت على تقدير جيد." not in r["escalation"]["confirmed"]


# ---- step 13c: live demo and v5 review, quotes after a rule sentence and in escalations ----

from tests.test_generation import CAL6, G17  # noqa: E402

CAL6_ROW = {**CAL6, "document_type": "calendar"}
HB10_DAMAGED = {"chunk_id": "HANDBOOK-1446#010", "source_id": "HANDBOOK-1446", "page": 18, "section": "الاعتذار عن الدراسة",
                "document_type": "regulation",
                "text": "4 الاعتذار عن الدراسة يجوز للطالب الاعتذار عن مواصلة دراسته لمدة فصل دراسي ) كالتالي: تكون الرسوم "
                        "الدراسية للفرصة الإضافية خمسة آلاف4( ريال عن كل فصل دراسي إضافي للموعد الأخير للاعتذار."}
HB17_EXAM = {"chunk_id": "HANDBOOK-1446#017", "source_id": "HANDBOOK-1446", "page": 23, "section": "الغياب عن الاختبار النهائي",
             "document_type": "regulation",
             "text": "في حال تغيب الطالب عن الاختبار النهائي وقبل عذره من مجلسي القسم والكلية، يعاد اختباره قبل نهاية الفصل التالي."}


def test_rule_backed_answer_quotes_only_the_calendar_row():
    r = assistant("SEMESTER_WITHDRAWAL", [CAL6_ROW, HB10_DAMAGED, G17], error=ValueError("bad json")).answer(
        "متى آخر موعد للاعتذار عن الفصل الدراسي الأول؟", "2026-10-14")
    assert r["status"] == "ANSWERABLE" and r["_trace"]["mode"] == "extractive"
    assert r["answer"].startswith("آخر موعد للاعتذار عن الفصل الدراسي الأول هو الخميس 2026-11-19")
    assert "خمسة آلاف" not in r["answer"]
    assert [q["chunk_id"] for q in r["_trace"]["quotes"]] == ["CALENDAR-1448#006"]


def test_rule_sentence_alone_when_no_calendar_row_qualifies():
    r = assistant("SEMESTER_WITHDRAWAL", [HB10_DAMAGED], error=ValueError("bad json")).answer(
        "متى آخر موعد للاعتذار عن الفصل الدراسي الأول؟", "2026-10-14")
    assert r["status"] == "ANSWERABLE" and r["_trace"]["quotes"] == []
    assert "«" not in r["answer"] and "2026-11-19" in r["answer"]


def test_escalation_shows_rule_sentence_but_no_quote_on_another_topic():
    # v5: after the attendance rule, a sentence on re-sitting a missed exam could read as permission.
    r = assistant("ATTENDANCE", [HB16, HB17_EXAM], {"answer": "x", "used_evidence": []}).answer(
        "نسبة حضوري 55% وعندي عذر طبي، هل أقدر أدخل النهائي؟", "2026-10-14")
    assert r["status"] == "STAFF_REVIEW_REQUIRED"
    confirmed = r["escalation"]["confirmed"]
    assert confirmed and confirmed == r["_trace"]["rule_texts"]
    assert not any("يعاد اختباره" in c for c in confirmed)
