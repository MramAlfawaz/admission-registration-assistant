"""Combine rankings with reciprocal rank fusion."""


def rank(scores, allowed, limit, positive_only=False):
    """Return the indices of the best-scoring allowed chunks, best first.

    Args:
        scores: one score per chunk.
        allowed: indices that may be returned (versions in force).
        limit: maximum number of indices.
        positive_only: drop chunks scoring 0 or less; used for BM25, where a
            zero score means the chunk shares no word with the question.
    """
    pool = [i for i in allowed if scores[i] > 0] if positive_only else list(allowed)
    return sorted(pool, key=lambda i: (-scores[i], i))[:limit]


def reciprocal_rank_fusion(rankings, k=60):
    """Fuse ranked index lists: each list adds 1 / (k + position) to an item's score.

    Args:
        rankings: lists of chunk indices, best first.
        k: damping constant; 60 is the value from the original RRF paper.

    Returns:
        Chunk indices ordered by fused score, best first.
    """
    fused = {}
    for ranking in rankings:
        for position, index in enumerate(ranking, 1):
            fused[index] = fused.get(index, 0.0) + 1.0 / (k + position)
    return sorted(fused, key=lambda i: (-fused[i], i))
