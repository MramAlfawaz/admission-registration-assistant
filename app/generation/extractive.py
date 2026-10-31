"""Fallback answer: quote the evidence sentences closest to the question."""
import re

from app.documents.normalize import normalize_for_search
from app.retrieval.tokenize import tokenize

MIN_QUOTE_TOKENS = 6
# Words that appear in almost every passage; sharing only these does not make a quote relevant.
GENERIC = {"فصل", "دراسي", "دراسيه", "دراسه", "طالب", "طلاب", "طلبه", "جامعه", "برنامج", "برامج", "مقرر",
           "مقررات", "موعد", "اخر", "يمكن", "يمكنني", "ابغي", "اريد", "شروط", "مطلوب", "مطلوبه", "يوجد",
           "هناك", "عام", "اول", "ثاني", "طلب", "يجب", "ايش", "كيف", "لائحه", "لوائح", "نظام", "انظمه",
           "عندكم", "ممكن", "لازم", "عشان", "قديش", "تبغي", "ابي", "اقدر", "يمكنني", "جامعتكم"}


def split_sentences(text):
    """Split passage text into sentences of readable length.

    Lines are joined first: PDF layout often moves a number such as 75% onto the
    next line, and splitting on line breaks would cut it off its sentence.
    """
    sentences = []
    for p in re.split(r"[.؛]", " ".join(text.split())):
        s = p.strip(" .،")
        if 20 <= len(s) <= 450 and len(tokenize(s)) >= MIN_QUOTE_TOKENS:
            sentences.append(s)
    return sentences


def overlap_scorer(question, sentences):
    """Score sentences by shared search tokens with the question."""
    q = set(tokenize(question))
    return [len(q & set(tokenize(s))) for s in sentences]


def embedding_scorer(encoder):
    """Return a scorer using the pinned embedding model; works across languages."""
    def score(question, sentences):
        if not sentences:
            return []
        vectors = encoder.encode(["query: " + question] + ["passage: " + s for s in sentences])
        return list(vectors[1:] @ vectors[0])
    return score


def same_word(a, b):
    """True when two search tokens are the same word, allowing Arabic suffixes (انذار ~ انذارين)."""
    if a == b:
        return True
    short, long_ = sorted((a, b), key=len)
    return len(short) >= 4 and long_.startswith(short)


def _has(tokens, wanted):
    """True when tokens contain the word `wanted`, or every word of a list `wanted`."""
    if isinstance(wanted, str):
        return any(same_word(wanted, t) for t in tokens)
    return all(_has(tokens, w) for w in wanted)


def relevance_filter(question, glossary=()):
    """Return a predicate that accepts only sentences sharing the question's key terms.

    A question naming a glossary term (in Arabic or English) needs a sentence with all
    the words of at least one such term. Otherwise the sentence must share one
    non-generic Arabic word with the question. An English question with no glossary
    term therefore gets no quotes: quoting unrelated Arabic text is worse than saying
    the evidence is insufficient (real failure R019, 2026-10-31).
    """
    q_tokens = tokenize(question)
    lowered = question.lower()
    terms = [tokenize(ar) for ar, en in glossary
             if (tokenize(ar) and _has(q_tokens, tokenize(ar))) or en.lower() in lowered]
    words = [t for t in q_tokens if t not in GENERIC and not t.isascii()]

    def qualifies(sentence):
        tokens = tokenize(sentence)
        if terms:
            return any(_has(tokens, term) for term in terms)
        return any(_has(tokens, w) for w in words)
    return qualifies


def select_sentences(question, evidence, scorer=overlap_scorer, k=2, min_score=1e-9, qualifies=None):
    """Return up to k (sentence, chunk) pairs from the evidence, best first.

    Args:
        question: the student question.
        evidence: validated chunks, best first.
        scorer: function(question, sentences) -> scores.
        k: maximum number of sentences.
        min_score: sentences scoring at or below this are ignored.
        qualifies: optional predicate; sentences it rejects are never quoted.
    """
    pairs = [(s, c) for c in evidence for s in split_sentences(c["text"]) if qualifies is None or qualifies(s)]
    if not pairs:
        return []
    scores = scorer(question, [s for s, _ in pairs])
    ranked = sorted(zip(scores, range(len(pairs))), key=lambda x: (-x[0], x[1]))
    return [pairs[i] for score, i in ranked[:k] if score > min_score]


def evidence_fits(question, texts, glossary=()):
    """True when the evidence shares the question's key terms; False means do not answer from it.

    Real failures (end-to-end v1): a flight-ticket question answered with supplementary-semester
    rules, an absent regulation answered with unrelated quotes. A question naming a glossary term
    needs a passage with that term. An Arabic question needs at least two of its key words (or
    its only one) in the evidence and a third of them overall. An English question with no
    glossary term cannot be compared word by word with Arabic text and is let through.
    """
    if not texts:
        return False
    ev_tokens = _with_bare(tokenize(" ".join(texts)))
    q_tokens = tokenize(question)
    lowered = question.lower()
    terms = [tokenize(ar) for ar, en in glossary
             if (tokenize(ar) and _has(q_tokens, tokenize(ar))) or en.lower() in lowered]
    if terms:
        return any(_has(ev_tokens, term) for term in terms)
    words = sorted({_bare(t) for t in q_tokens if t not in GENERIC and not t.isascii() and len(t) > 2})
    if not words:
        return True
    shared = sum(1 for w in words if _has(ev_tokens, w))
    return shared >= 1 and shared / len(words) >= 1 / 3


def _bare(token):
    """Drop a one-letter proclitic (و ب ل ف ك) and a possessive ending, so بتقدير ~ تقدير and قيدي ~ قيد."""
    if len(token) >= 5 and token[0] in "وبلفك":
        token = token[1:]
    for ending in ("هم", "ها", "نا", "ي", "ه", "ك"):
        if len(token) - len(ending) >= 3 and token.endswith(ending):
            return token[: -len(ending)]
    return token


def _with_bare(tokens):
    return set(tokens) | {_bare(t) for t in tokens}


# A quote about the other term must not answer a question about this one (step 12 test: a question on the
# first term was answered with a second-term sentence). Patterns are on normalised text.
TERM_PATTERNS = {
    "T1": re.compile(r"(فصل|ترم)( الدراسي)? الاول|first (semester|term)|fall semester|(semester|term) 1\b"),
    "T2": re.compile(r"(فصل|ترم)( الدراسي)? الثاني|second (semester|term)|spring semester|(semester|term) 2\b"),
}


def mentions_other_term(sentence, term):
    """True when the sentence names the other term and not the one asked about."""
    if term not in TERM_PATTERNS:
        return False
    other = "T2" if term == "T1" else "T1"
    text = normalize_for_search(sentence)
    return bool(TERM_PATTERNS[other].search(text)) and not TERM_PATTERNS[term].search(text)


# Signs of text damaged by PDF extraction of mixed-direction lines (README, known limitations).
LATIN_WORD = re.compile(r"[A-Za-z]{2,}")
EMAIL_OR_URL = re.compile(r"\S+@\S+|https?://\S+|www\.\S+")
GLUED = re.compile(r"[\u0621-\u064A]\d|\d[\u0621-\u0644\u0646\u0648-\u064A]")  # word48, 00ح (not 2026م, 1448هـ)
ARABIC_LETTER = re.compile(r"[\u0621-\u064A]")


def readable(sentence):
    """False when a sentence shows extraction damage: reversed or empty brackets, numbers glued to
    words, a leading number or bracket, or Latin words inside Arabic text (emails and links allowed)."""
    text = sentence.strip()
    if not text or text[0].isdigit() or text[0] in ")(]":
        return False
    depth = 0
    for ch in text:
        depth += {"(": 1, ")": -1}.get(ch, 0)
        if depth < 0:
            return False
    if depth != 0 or re.search(r"\(\s*\)", text) or GLUED.search(text):
        return False
    if len(ARABIC_LETTER.findall(text)) > len(re.findall(r"[A-Za-z]", text)):
        return len(LATIN_WORD.findall(EMAIL_OR_URL.sub(" ", text))) < 2
    return True
