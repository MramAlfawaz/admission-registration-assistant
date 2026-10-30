from app.generation.extractive import select_sentences
from app.intent.ambiguity import detect_missing
from app.safety.escalation import escalation_reason
from app.safety.verifier import verify_text

EVIDENCE = ["آخر موعد للاعتذار عن الفصل الدراسي الأول: الخميس 2026-11-19م", "نسبة الحضور 75%"]
CLOSED = [{"rule_id": "RULE-CAL-01", "output": "closed", "details": {"date": "2026-11-19"}}]


def test_clean_text_passes():
    assert verify_text("يقدم الطلب إلى رئيس القسم قبل الموعد.", "ar", EVIDENCE, []) == []


def test_foreign_script_rejected():
    assert any("foreign script" in i for i in verify_text("الطالب 需要 خبرة", "ar", EVIDENCE, []))


def test_numbers_must_come_from_evidence():
    assert verify_text("الحد الأدنى 75% وآخر موعد 2026-11-19", "ar", EVIDENCE, []) == []
    assert any("numbers not in evidence" in i for i in verify_text("الحد الأدنى 80%", "ar", EVIDENCE, []))


def test_weekday_must_come_from_evidence():
    assert verify_text("The deadline is Thursday.", "en", EVIDENCE, []) == []
    assert any("weekday" in i for i in verify_text("The deadline is Friday.", "en", EVIDENCE, []))


def test_identifier_decision_language_and_closed_advice():
    assert any("identifier" in i for i in verify_text("according to calendar-1448", "en", EVIDENCE, []))
    assert any("decision" in i for i in verify_text("You will be accepted.", "en", EVIDENCE, []))
    assert any("not mainly in English" in i for i in verify_text("الطالب يقدم الطلب", "en", EVIDENCE, []))
    assert any("closed" in i for i in verify_text("You can still submit it.", "en", EVIDENCE, CLOSED))


def test_extractive_picks_the_answering_sentence():
    chunk = {"chunk_id": "G#17", "source_id": "G", "text": "يقدم البرنامج باللغة العربية. "
             "أو أن تكون له خبرة عملية لا تقل عن ثلاث سنوات في أحد مجالات إنفاذ القانون."}
    picked = select_sentences("هل يحتاج ماجستير إنفاذ القانون خبرة عملية؟", [chunk], k=1)
    assert "ثلاث سنوات" in picked[0][0]


def test_ambiguity_only_from_question_text():
    assert detect_missing("هل أقدر أنسحب؟", "SEMESTER_WITHDRAWAL") == "withdrawal_scope"
    assert detect_missing("هل أقدر أنسحب من البرنامج؟", "PROGRAM_WITHDRAWAL") is None
    assert detect_missing("متى آخر موعد للاعتذار؟", "SEMESTER_WITHDRAWAL") is None
    assert detect_missing("هل أقدر أنسحب؟", "SEMESTER_WITHDRAWAL", {"withdrawal_scope": "course"}) is None
    assert detect_missing("كم مدة الدراسة؟", "STUDY_DURATION") == "degree_level"
    assert detect_missing("كم مدة ماجستير علم الجريمة؟", "STUDY_DURATION") is None
    assert detect_missing("What happens after two academic warnings?", "GRADUATION_REQUIREMENTS") is None


def test_escalation_reasons():
    assert escalation_reason("أطلب استثناء من شرط الحضور") == "decision"
    assert escalation_reason("Will I be accepted into the program?") == "decision"
    assert escalation_reason("كم معدلي التراكمي؟") == "personal_record"
    assert escalation_reason("كم نسبة الحضور المطلوبة؟") is None
    assert escalation_reason("x", [{"output": "exception_only"}]) == "exception_rule"


# ---- phase 10b: per-sentence filter ----
from pathlib import Path

from app.safety.sentence_filter import filter_items, filter_sentences, load_glossary, split_sentences

GLOSSARY = load_glossary(Path(__file__).resolve().parents[1] / "prompts" / "glossary_v1.md")
CTX = dict(language="ar", evidence_texts=EVIDENCE, rule_outputs=[], rule_texts=[],
           intent="SEMESTER_WITHDRAWAL", glossary=GLOSSARY, question="")


def test_glossary_loads_pairs():
    assert len(GLOSSARY) >= 10 and all(ar and en for ar, en in GLOSSARY)


def test_preamble_trimmed():
    assert split_sentences("بناءً على الأدلة، آخر موعد للاعتذار الخميس.") == ["آخر موعد للاعتذار الخميس."]


def test_each_sentence_judged_alone():
    text = "آخر موعد للاعتذار عن الفصل الدراسي الأول الخميس 2026-11-19. ربما يمكنك الانسحاب من البرنامج."
    kept, dropped = filter_sentences(text, **CTX)
    assert kept == ["آخر موعد للاعتذار عن الفصل الدراسي الأول الخميس 2026-11-19."]
    assert "speculation" in dropped[0][1]


def test_other_situation_and_ungrounded_term_dropped():
    _, dropped = filter_sentences("يمكنك دراسة الفصل التكميلي بعد الاعتذار.", **CTX)
    assert any(i.startswith("other situation") for i in dropped[0][1])
    ctx = dict(CTX, intent="ADMISSION_REQUIREMENTS")
    _, dropped = filter_sentences("يحصل الطالب على المرتبة الشرفية.", **ctx)
    assert any("term not in evidence" in i for i in dropped[0][1])


def test_conditions_must_be_grounded_sentences():
    items = ["تأجيل الدراسة", "conditions written in the evidence",
             "آخر موعد للاعتذار عن الفصل الدراسي الأول الخميس 2026-11-19"]
    assert filter_items(items, **CTX) == [items[2]]
