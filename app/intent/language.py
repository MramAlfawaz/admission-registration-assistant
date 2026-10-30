"""Detect whether a question is Arabic, English or mixed."""
import re

ARABIC = re.compile(r"[؀-ۿ]")
LATIN = re.compile(r"[A-Za-z]")


def detect_language(text):
    """Return "ar", "en" or "mixed" from the share of Arabic and Latin letters.

    Args:
        text: the question.

    Returns:
        "ar" or "en" when one script has at least 80% of the letters,
        "mixed" otherwise, and "ar" for text with no letters at all.
    """
    ar, en = len(ARABIC.findall(text)), len(LATIN.findall(text))
    total = ar + en
    if total == 0:
        return "ar"
    if ar / total >= 0.8:
        return "ar"
    if en / total >= 0.8:
        return "en"
    return "mixed"


def answer_language(text):
    """Return the language to answer in: the majority script of the question."""
    ar, en = len(ARABIC.findall(text)), len(LATIN.findall(text))
    return "en" if en > ar else "ar"
