import pytest

from app.documents.registry import add_source
from app.documents.version_selector import current_version

OLD = {"source_id": "CALENDAR-1448", "title": "t", "document_type": "calendar",
       "authority_level": 2, "version": "1448", "effective_from": "2026-08-12",
       "effective_to": None, "language": "ar", "status": "approved", "filename": "a.pdf"}
NEW = {"source_id": "CALENDAR-1449", "title": "t", "document_type": "calendar",
       "authority_level": 2, "version": "1449", "effective_from": "2027-08-22",
       "language": "ar", "filename": "b.pdf", "supersedes": "CALENDAR-1448"}


def test_new_version_closes_old_one():
    sources = add_source([OLD], NEW)
    old = sources[0]
    assert old["effective_to"] == "2027-08-21" and old["status"] == "superseded"
    assert current_version(sources, "CALENDAR", "2027-08-21")["source_id"] == "CALENDAR-1448"
    assert current_version(sources, "CALENDAR", "2027-08-22")["source_id"] == "CALENDAR-1449"


def test_original_list_is_not_modified():
    add_source([OLD], NEW)
    assert OLD["effective_to"] is None


def test_duplicate_id_rejected():
    with pytest.raises(ValueError):
        add_source([OLD], {**NEW, "source_id": "CALENDAR-1448"})


def test_unknown_superseded_rejected():
    with pytest.raises(ValueError):
        add_source([OLD], {**NEW, "supersedes": "NOPE"})


def test_missing_field_rejected():
    with pytest.raises(ValueError):
        add_source([OLD], {k: v for k, v in NEW.items() if k != "effective_from"})
