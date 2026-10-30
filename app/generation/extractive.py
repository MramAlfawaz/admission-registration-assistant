"""Fallback answer: quote the evidence sentences closest to the question."""
import re

from app.retrieval.tokenize import tokenize


def split_sentences(text):
    """Split passage text into sentences of readable length."""
    sentences = []
    for p in re.split(r"[.\n؛]", text):
        s = " ".join(p.split()).strip(" .،")
        if 20 <= len(s) <= 350:
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


def select_sentences(question, evidence, scorer=overlap_scorer, k=2, min_score=1e-9):
    """Return up to k (sentence, chunk) pairs from the evidence, best first.

    Args:
        question: the student question.
        evidence: validated chunks, best first.
        scorer: function(question, sentences) -> scores.
        k: maximum number of sentences.
        min_score: sentences scoring at or below this are ignored.
    """
    pairs = [(s, c) for c in evidence for s in split_sentences(c["text"])]
    if not pairs:
        return []
    scores = scorer(question, [s for s, _ in pairs])
    ranked = sorted(zip(scores, range(len(pairs))), key=lambda x: (-x[0], x[1]))
    return [pairs[i] for score, i in ranked[:k] if score > min_score]
