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
