"""Fallback answer: quote the evidence sentences closest to the question."""
import re

from app.retrieval.tokenize import tokenize

MIN_QUOTE_TOKENS = 6
# Words that appear in almost every passage; sharing only these does not make a quote relevant.
GENERIC = {"فصل", "دراسي", "دراسيه", "دراسه", "طالب", "طلاب", "طلبه", "جامعه", "برنامج", "برامج", "مقرر",
           "مقررات", "موعد", "اخر", "يمكن", "يمكنني", "ابغي", "اريد", "شروط", "مطلوب", "مطلوبه", "يوجد",
           "هناك", "عام", "اول", "ثاني", "طلب", "يجب", "ايش", "كيف"}


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
