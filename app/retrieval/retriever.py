"""Search chunks restricted to the document versions in force on a date."""
from app.documents.version_selector import select_sources
from app.retrieval.hybrid import rank, reciprocal_rank_fusion

METHODS = ("bm25", "embeddings", "hybrid")


class Retriever:
    """Return the top chunks for a question, never from a version not in force."""

    def __init__(self, chunks, sources, bm25=None, embeddings=None, candidates=50, rrf_k=60):
        self.chunks, self.sources = chunks, sources
        self.bm25, self.embeddings = bm25, embeddings
        self.candidates, self.rrf_k = candidates, rrf_k

    def allowed_indices(self, as_of):
        """Return indices of chunks whose source is in force on as_of."""
        in_force = {s["source_id"] for s in select_sources(self.sources, as_of)}
        return [i for i, c in enumerate(self.chunks) if c["source_id"] in in_force]

    def search(self, query, as_of, method="hybrid", k=10):
        """Return up to k chunks for a query, best first.

        Args:
            query: the student question.
            as_of: the date the question is about (ISO string or date).
            method: "bm25", "embeddings" or "hybrid".
            k: number of chunks to return.

        Returns:
            A list of chunk dictionaries.
        """
        allowed = self.allowed_indices(as_of)
        if method == "bm25":
            order = rank(self.bm25.scores(query), allowed, k, positive_only=True)
        elif method == "embeddings":
            order = rank(self.embeddings.scores(query), allowed, k)
        elif method == "hybrid":
            order = reciprocal_rank_fusion(
                [rank(self.bm25.scores(query), allowed, self.candidates, positive_only=True),
                 rank(self.embeddings.scores(query), allowed, self.candidates)],
                self.rrf_k)[:k]
        else:
            raise ValueError(f"unknown method: {method}")
        return [self.chunks[i] for i in order]
