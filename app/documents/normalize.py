"""Clean extracted text and prepare it for search."""
import re
import unicodedata

TATWEEL = "\u0640"
DIACRITICS = re.compile(r"[\u064B-\u0652]")
ZERO_WIDTH = dict.fromkeys(map(ord, "\u200b\u200c\u200d\u200e\u200f\ufeff"))


def clean_text(text):
    """Remove extraction artefacts while keeping the original wording.

    Args:
        text: extracted text.

    Returns:
        Text with presentation forms unified, tatweel and zero-width
        characters removed, and spaces collapsed.
    """
    text = unicodedata.normalize("NFKC", text)
    text = text.replace(TATWEEL, "").translate(ZERO_WIDTH)
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.splitlines()]
    return "\n".join(lines)


def normalize_for_search(text):
    """Return a form of the text used only for matching, never for display.

    Args:
        text: any Arabic or English text.

    Returns:
        Lowercased text with diacritics removed and letter variants unified.
    """
    text = DIACRITICS.sub("", clean_text(text))
    text = re.sub("[أإآ]", "ا", text)
    text = text.replace("ة", "ه").replace("ى", "ي")
    return text.lower()
