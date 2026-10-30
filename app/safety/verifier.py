"""Check model-written text before it reaches a student (Stage 7 of the brief).

Every check here can only reject text; none of them can make an answer
more confident. A rejected text is replaced by quoted evidence.
"""
import re

from app.documents.normalize import normalize_for_search

ARABIC_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
# Arabic, Latin, digits, whitespace and common punctuation; anything else (CJK, Cyrillic...) is rejected.
ALLOWED = re.compile(r"[؀-ۿݐ-ݿﭐ-﷿ﹰ-﻿A-Za-z0-9\s"
                     r".,;:!?%()\[\]{}\-–—/'\"«»“”‘’+*&@#_=<>|~^$ ‌‏‎]")
WEEKDAYS_AR = ["الاحد", "الاثنين", "الثلاثاء", "الاربعاء", "الخميس", "الجمعه", "السبت"]
WEEKDAYS_EN = ["sunday", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday"]
LEAKED_ID = re.compile(r"(calendar|handbook|programs?-guide|faq-nauss|admission-page)[-_ ]?\d*|\[E\d+\]", re.I)
NO_INFO = ["لا يوجد في النص", "لا توجد معلومات", "لا يمكن تحديد", "غير مذكور", "لا تتوفر معلومات", "لا تذكر",
           "no information", "not mentioned", "cannot determine", "does not specify", "not specified",
           "does not mention", "no mention"]
DECISION = ["تم قبولك", "سيتم قبولك", "انت مقبول", "تمت الموافقه", "ستتم الموافقه", "سيتم الموافقه",
            "تم اعتماد", "يحق لك الاستثناء", "مؤهل للقبول",
            "you are accepted", "you will be accepted", "you are admitted", "you will be admitted",
            "has been approved", "will be approved", "you qualify for admission", "your request will be"]
SUBMIT = ["قدم الطلب", "تقديم طلب", "يجب تقديم", "يمكنك التقديم", "قدم اعتذار", "submit", "apply now", "you can still"]


def _numbers(text):
    """Return the set of number tokens in a text, with date parts split out."""
    text = text.translate(ARABIC_DIGITS)
    found = set()
    for token in re.findall(r"\d[\d,]*(?:\.\d+)?", text):
        token = token.replace(",", "")
        found.add(token.rstrip("0").rstrip(".") if "." in token else token)
        found.update(p.lstrip("0") or "0" for p in re.split(r"\D", token) if p)
    for date in re.findall(r"\d{4}-\d{2}-\d{2}", text):
        found.update(p.lstrip("0") for p in date.split("-"))
    return found


def verify_text(text, language, evidence_texts, rule_outputs, question=""):
    """Return a list of issues found in model-written text; empty means it may be shown.

    Args:
        text: the model's explanation, conditions and required action, joined.
        language: "ar" or "en", the language the answer must be in.
        evidence_texts: texts of the passages the model was given, plus rule sentences.
        rule_outputs: rule engine results used for the answer.
        question: the student question; numbers the student wrote are allowed.
    """
    issues = []
    if not text.strip():
        return issues
    bad = sorted({ch for ch in text if not ALLOWED.match(ch)})
    if bad:
        issues.append(f"foreign script: {''.join(bad[:10])}")
    letters = re.findall(r"[؀-ۿA-Za-z]", text)
    arabic = sum(1 for ch in letters if "؀" <= ch <= "ۿ")
    if letters and language == "ar" and arabic / len(letters) < 0.6:
        issues.append("answer is not mainly in Arabic")
    if letters and language == "en" and arabic / len(letters) > 0.2:
        issues.append("answer is not mainly in English")
    if LEAKED_ID.search(text):
        issues.append(f"internal identifier shown: {LEAKED_ID.search(text).group(0)}")
    allowed = set()
    for t in list(evidence_texts) + [question]:
        allowed |= _numbers(t)
    for r in rule_outputs:
        for v in r["details"].values():
            allowed |= _numbers(str(v))
    unsupported = sorted(n for n in _numbers(text) - allowed if len(n) > 0)
    if unsupported:
        issues.append(f"numbers not in evidence: {', '.join(unsupported[:8])}")
    norm = normalize_for_search(text)
    evidence_norm = normalize_for_search(" ".join(evidence_texts))
    days_in_evidence = {WEEKDAYS_EN[i] for i, d in enumerate(WEEKDAYS_AR) if d in evidence_norm} | \
                       {d for d in WEEKDAYS_EN if d in evidence_norm}
    for i, (ar, en) in enumerate(zip(WEEKDAYS_AR, WEEKDAYS_EN)):
        if (ar in norm or en in norm) and en not in days_in_evidence:
            issues.append(f"weekday not in evidence: {en}")
    if any(p in norm for p in NO_INFO):
        issues.append("claims there is no information although evidence was found")
    if any(p in norm for p in DECISION):
        issues.append("states or implies an official decision")
    closed = any(r["output"] in ("closed", "refund_not_eligible") for r in rule_outputs)
    if closed and any(p in norm for p in SUBMIT):
        issues.append("advises acting although the period has closed")
    return issues
