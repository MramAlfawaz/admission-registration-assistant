"""Turn Arabic and English text into search tokens for BM25."""
import re

from app.documents.normalize import normalize_for_search

# Written in search form (normalize_for_search): ى -> ي, ة -> ه, أإآ -> ا.
STOPWORDS = {
    "في", "من", "علي", "عن", "الي", "هل", "ما", "ماذا", "متي", "كيف", "كم", "هو", "هي",
    "ان", "او", "ثم", "لا", "لم", "لن", "قد", "كل", "هذا", "هذه", "ذلك", "التي", "الذي",
    "مع", "بعد", "قبل", "عند", "اذا", "وش", "ابي", "اقدر", "يحق", "لي", "عندي", "انا",
    "the", "a", "an", "of", "to", "in", "on", "for", "is", "are", "do", "does", "i", "my",
    "can", "what", "when", "how", "and", "or", "if", "it", "be", "with", "from", "at",
}
PREFIXES = ("وال", "بال", "كال", "فال", "لل", "ال")
# Arabic letters and Arabic-Indic digits only, so punctuation such as ؟ ، ؛ never sticks to a word.
TOKEN = re.compile(r"[\u0621-\u063A\u0641-\u064A\u0660-\u0669]+|[a-z0-9]+")


def tokenize(text):
    """Return lowercase tokens with stopwords removed and Arabic article prefixes stripped.

    Args:
        text: any Arabic or English text.

    Returns:
        A list of tokens.
    """
    tokens = []
    for token in TOKEN.findall(normalize_for_search(text)):
        if token in STOPWORDS:
            continue
        for prefix in PREFIXES:
            if token.startswith(prefix) and len(token) - len(prefix) >= 3:
                token = token[len(prefix):]
                break
        if len(token) > 1:
            tokens.append(token)
    return tokens
