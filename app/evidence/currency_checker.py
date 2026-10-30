"""Reject evidence from document versions not in force on the query date."""
from app.documents.version_selector import in_force


def check_currency(chunks, sources_by_id, as_of):
    """Split chunks into those in force on as_of and those rejected.

    Retrieval already filters by date; this second check catches any defect
    upstream, because a superseded rule reaching the answer is the failure the
    brief names first.

    Args:
        chunks: retrieved chunk dictionaries.
        sources_by_id: source metadata keyed by source_id.
        as_of: the date the question is about.

    Returns:
        A (current, rejected) pair; each rejected item carries a reason.
    """
    current, rejected = [], []
    for c in chunks:
        source = sources_by_id.get(c["source_id"])
        if source is None:
            rejected.append({"chunk_id": c["chunk_id"], "reason": "unknown source"})
        elif not in_force(source, as_of):
            rejected.append({"chunk_id": c["chunk_id"], "reason": f"not in force on {as_of}"})
        else:
            current.append(c)
    return current, rejected
