"""Extract checkable facts (durations, amounts, percentages, GPAs, dates) from passages."""
import re
from dataclasses import dataclass, field

from app.documents.normalize import normalize_for_search
from app.evidence.subject import extract_subject

ARABIC_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
MONTHS = {"يناير": 1, "فبراير": 2, "مارس": 3, "ابريل": 4, "مايو": 5, "يونيو": 6, "يوليو": 7,
          "اغسطس": 8, "سبتمبر": 9, "اكتوبر": 10, "نوفمبر": 11, "ديسمبر": 12,
          "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6, "july": 7,
          "august": 8, "september": 9, "october": 10, "november": 11, "december": 12}
# Duration phrases mapped to a number of semesters; longest first.
DURATIONS = [("اربع سنوات", 8), ("ثمانيه فصول", 8), ("اربعه فصول", 4), ("عامان", 4),
             ("سنتان", 4), ("عام دراسي", 2), ("سنه دراسيه", 2), ("فصلان", 2), ("عام واحد", 2)]
FEE_KINDS = [("application", ["طلب التقديم", "رسوم التقديم", "رسم التقديم"]),
             ("administrative", ["اداريه"]),
             ("extra_semester", ["اضافي", "الفرصه"]),
             ("supplementary", ["تكميلي"]),
             ("tuition", ["الرسوم الدراسيه", "رسوم دراسيه", "الرسوم الدراسيه للبرنامج"])]
GPA_KINDS = [("warning", ["انذار"]), ("supplementary", ["تكميلي"]),
             ("graduation", ["تخرج", "متطلبات", "اجتياز الساعات"])]
EVENTS = [("semester_withdrawal", ["اعتذار"]), ("postponement", ["تاجيل"]),
          ("reenrollment", ["اعاده القيد"]), ("final_exams_start", ["بدايه الاختبارات"]),
          ("final_exams_end", ["نهايه الاختبارات"]), ("term_start", ["بدايه الدراسه"])]


@dataclass
class Fact:
    """One checkable statement: a typed value, its kind, its subject and where it came from."""
    type: str
    kind: str
    value: object
    subject: dict = field(default_factory=dict)
    source_id: str = ""
    chunk_id: str = ""
    span: str = ""


def _kind(window, options, default="unknown"):
    for kind, keywords in options:
        if any(k in window for k in keywords):
            return kind
    return default


def _facts(text):
    """Yield (type, kind, value, start, end) tuples found in normalized text."""
    for phrase, semesters in DURATIONS:
        for m in re.finditer(phrase, text):
            if "مده" in text[max(0, m.start() - 45):m.start()]:
                yield "duration", "study_duration", semesters, m.start(), m.end()
    for m in re.finditer(r"(\d[\d,]*)\s*(?=[^\d]{0,25}ريال)|(?<=ريال)[^\d]{0,25}?(\d[\d,]*)", text):
        raw = (m.group(1) or m.group(2) or "").replace(",", "")
        if raw.isdigit():
            window = text[max(0, m.start() - 60):m.end() + 60]
            yield "money", _kind(window, FEE_KINDS), int(raw), m.start(), m.end()
    for m in re.finditer(r"(\d{1,3})\s*%|%\s*(\d{1,3})|(\d{1,3})\s*بالمائه", text):
        value = int(m.group(1) or m.group(2) or m.group(3))
        window = text[max(0, m.start() - 80):m.end() + 40]
        yield "percent", "attendance" if ("حضور" in window or "غياب" in window) else "other", value, m.start(), m.end()
    for m in re.finditer(r"(\d[.,]\d{1,2})\s*من\s*5|5\s*من\s*(\d[.,]\d{1,2})", text):
        value = float((m.group(1) or m.group(2)).replace(",", "."))
        window = text[max(0, m.start() - 80):m.end() + 80]
        yield "gpa", _kind(window, GPA_KINDS, "other"), value, m.start(), m.end()
    for m in re.finditer(r"(\d{4})-(\d{2})-(\d{2})", text):
        window = text[max(0, m.start() - 80):m.start()]
        yield "date", _kind(window, EVENTS), f"{int(m.group(2)):02d}-{int(m.group(3)):02d}|{m.group(1)}", m.start(), m.end()
    month_names = "|".join(MONTHS)
    for m in re.finditer(rf"(\d{{1,2}})\s+({month_names})(?:\s+(\d{{4}}))?", text):
        window = text[max(0, m.start() - 80):m.start()]
        value = f"{MONTHS[m.group(2)]:02d}-{int(m.group(1)):02d}|{m.group(3) or ''}"
        yield "date", _kind(window, EVENTS), value, m.start(), m.end()


def extract_facts(chunk):
    """Return the facts stated in a chunk, each with the subject of its local context.

    Args:
        chunk: a chunk dictionary with "text", "source_id" and "chunk_id".

    Returns:
        A list of Fact objects.
    """
    text = normalize_for_search(chunk["text"]).translate(ARABIC_DIGITS)
    found = []
    for ftype, kind, value, start, end in _facts(text):
        subject = extract_subject(text[max(0, start - 100):start])
        found.append(Fact(ftype, kind, value, subject, chunk.get("source_id", ""),
                          chunk.get("chunk_id", ""), text[max(0, start - 40):end + 20]))
    return found


def same_value(a, b):
    """Compare two fact values; dates without a year compare on month and day only."""
    if isinstance(a, str) and isinstance(b, str) and "|" in a and "|" in b:
        (md_a, y_a), (md_b, y_b) = a.split("|"), b.split("|")
        return md_a == md_b and (not y_a or not y_b or y_a == y_b)
    return a == b
