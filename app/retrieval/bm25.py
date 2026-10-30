"""Keyword retrieval with BM25."""
from rank_bm25 import BM25Okapi

from app.retrieval.tokenize import tokenize


def passage_text(chunk):
    """Return the text indexed for a chunk: its section heading and body."""
    return f"{chunk.get('section') or ''}\n{chunk['text']}"


class BM25Index:
    """Score every chunk against a query with BM25."""

    def __init__(self, chunks):
        self.bm25 = BM25Okapi([tokenize(passage_text(c)) or ["_"] for c in chunks])

    def scores(self, query):
        """Return one BM25 score per chunk, in chunk order."""
        return list(self.bm25.get_scores(tokenize(query)))
