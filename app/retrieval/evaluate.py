"""Measure retrieval against the gold set: Recall@k and Precision@5 per language."""
import json
from pathlib import Path


def load_gold(path):
    """Read gold questions; each has evidence groups of acceptable chunk ids."""
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line]


def score_question(gold, retrieved_ids):
    """Return recall@5, recall@10 and precision@5 for one question.

    Recall@k is the share of evidence groups with at least one chunk in the
    top k. Precision@5 is the share of the top 5 that belongs to any group.
    """
    groups = [set(g) for g in gold["evidence"]]
    relevant = set().union(*groups)

    def recall(k):
        top = set(retrieved_ids[:k])
        return sum(bool(g & top) for g in groups) / len(groups)

    top5 = retrieved_ids[:5]
    return {"recall@5": recall(5), "recall@10": recall(10),
            "precision@5": sum(c in relevant for c in top5) / 5}


def _mean(rows, key):
    return round(sum(r[key] for r in rows) / len(rows), 4) if rows else None


def summarise(rows):
    """Average per-question metrics."""
    return {"n": len(rows), **{k: _mean(rows, k) for k in ("recall@5", "recall@10", "precision@5")}}


def suggest_cause(gold, retrieved, allowed_sources):
    """Give a first guess at why a question missed; a person confirms it later."""
    wanted = {cid.split("#")[0] for g in gold["evidence"] for cid in g}
    if not wanted & allowed_sources:
        return "version filtering error"
    if gold["language"] == "en":
        return "cross-language vocabulary mismatch"
    if any(c["source_id"] in wanted for c in retrieved):
        return "wrong section or chunk granularity"
    return "vocabulary mismatch"


def evaluate(retriever, gold_rows, method):
    """Run every gold question and return overall, per-language and failure results."""
    per_question, failures, leaks = [], [], 0
    for g in gold_rows:
        retrieved = retriever.search(g["question"], g["as_of"], method=method, k=10)
        ids = [c["chunk_id"] for c in retrieved]
        allowed = {c["source_id"] for c in (retriever.chunks[i] for i in retriever.allowed_indices(g["as_of"]))}
        leaks += sum(c["source_id"] not in allowed for c in retrieved)
        m = {"id": g["id"], "language": g["language"], **score_question(g, ids)}
        per_question.append(m)
        if m["recall@10"] < 1:
            failures.append({"id": g["id"], "question": g["question"], "as_of": g["as_of"],
                             "expected": g["evidence"], "retrieved_top5": ids[:5],
                             "suggested_cause": suggest_cause(g, retrieved, allowed)})
    result = {"method": method, "overall": summarise(per_question),
              "version_leaks": leaks, "failures": failures, "per_question": per_question}
    for lang in sorted({q["language"] for q in per_question}):
        result[lang] = summarise([q for q in per_question if q["language"] == lang])
    return result
