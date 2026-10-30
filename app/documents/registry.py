"""Add new document versions to the source registry without code changes."""
import datetime as dt

REQUIRED = ("source_id", "title", "document_type", "authority_level", "version",
            "effective_from", "language", "filename")


def add_source(sources, new):
    """Return the registry with a new source added and its predecessor closed.

    The superseded source gets effective_to set to the day before the new
    version starts and its status set to "superseded". It stays in the
    registry so questions about past dates still use it.

    Args:
        sources: current list of source metadata dictionaries.
        new: metadata of the new source.

    Returns:
        A new list of sources.

    Raises:
        ValueError: if a field is missing, the id exists, or the superseded id is unknown.
    """
    missing = [k for k in REQUIRED if not new.get(k)]
    if missing:
        raise ValueError(f"missing fields: {', '.join(missing)}")
    if any(s["source_id"] == new["source_id"] for s in sources):
        raise ValueError(f"source_id already exists: {new['source_id']}")
    updated = [dict(s) for s in sources]
    old_id = new.get("supersedes")
    if old_id:
        old = next((s for s in updated if s["source_id"] == old_id), None)
        if old is None:
            raise ValueError(f"superseded source not found: {old_id}")
        start = dt.date.fromisoformat(new["effective_from"])
        old["effective_to"] = (start - dt.timedelta(days=1)).isoformat()
        old["status"] = "superseded"
    entry = {"effective_to": None, "status": "approved", "supersedes": None,
             "dates_assumed": False, "url": None, **new}
    return updated + [entry]
