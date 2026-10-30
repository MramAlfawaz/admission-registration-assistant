"""Identify who or what a question or a fact is about: degree, program, term."""
from app.documents.normalize import normalize_for_search

# Keywords in search form (normalize_for_search). Longer, more specific names first.
DEGREES = [
    ("phd", ["دكتوراه", "دكتوراة", "phd", "doctor"]),
    ("diploma", ["الدبلوم", "دبلوم", "diploma"]),
    ("master", ["ماجستير", "ماجيستير", "master"]),
]
PROGRAMS = [
    ("criminology", ["علم الجريمه", "criminology"]),
    ("national_security", ["الامن الوطني", "national security"]),
    ("cybercrime", ["الجرائم السيبرانيه", "cybercrime", "cyber"]),
    ("secure_ai", ["الذكاء الاصطناعي", "artificial intelligence", "secure ai", " ai "]),
    ("economic_crimes", ["الجرائم الاقتصاديه", "economic crime"]),
    ("law_enforcement", ["انفاذ القانون", "law enforcement"]),
    ("forensic", ["الادله الجنائيه", "forensic"]),
    ("human_rights", ["حقوق الانسان", "human rights"]),
    ("counter_terrorism", ["مكافحه الارهاب", "terrorism"]),
    ("border_security", ["امن الحدود", "border"]),
    ("drug_control", ["المخدرات", "drug"]),
    ("criminal_law", ["القانون الجنائي", "criminal law"]),
]
TERMS = [
    ("T1", ["الفصل الاول", "الفصل الدراسي الاول", "الترم الاول", "first semester", "first term"]),
    ("T2", ["الفصل الثاني", "الفصل الدراسي الثاني", "الترم الثاني", "second semester", "second term"]),
]


def _nearest(text, options):
    """Return the option mentioned closest to the end of text, or None.

    Facts pass the text before their value, so the closest mention wins: in
    "durations for master's and diploma ... master's: two years" the value
    belongs to the master's, not to the first degree named.
    """
    best, best_pos = None, -1
    for value, keywords in options:
        pos = max(text.rfind(k) for k in keywords)
        if pos > best_pos:
            best, best_pos = value, pos
    return best


def extract_subject(text):
    """Return the degree, program and term named in a text, None for each one absent.

    When a text names several, the one closest to its end is returned.

    Args:
        text: a question or the context around a fact.

    Returns:
        A dict with keys "degree", "program" and "term".
    """
    t = f" {normalize_for_search(text)} "
    return {"degree": _nearest(t, DEGREES), "program": _nearest(t, PROGRAMS), "term": _nearest(t, TERMS)}


def compatible(a, b):
    """Return True when two subjects could describe the same thing.

    A field counts against compatibility only when both sides name it and the
    names differ; a missing value means the statement is general.
    """
    return all(a.get(k) is None or b.get(k) is None or a[k] == b[k]
               for k in ("degree", "program", "term"))
