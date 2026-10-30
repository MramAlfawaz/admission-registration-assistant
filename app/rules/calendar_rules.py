"""Date rules computed from the academic calendar in force on the query date."""
import datetime as dt
import json
from pathlib import Path

from app.documents.version_selector import select_sources


def _date(value):
    return value if isinstance(value, dt.date) else dt.date.fromisoformat(value)


class CalendarStore:
    """Give access to the structured events of the calendar in force on a date."""

    def __init__(self, events_by_source, sources):
        self.events_by_source = events_by_source
        self.sources = sources

    @classmethod
    def from_dir(cls, calendar_dir, sources):
        """Load every <source_id>.json written by 'python cli.py build-calendar'."""
        events = {p.stem: json.loads(p.read_text(encoding="utf-8")) for p in Path(calendar_dir).glob("*.json")}
        return cls(events, sources)

    def calendar_for(self, as_of):
        """Return (source, events) for the calendar in force on as_of, or (None, [])."""
        for s in select_sources(self.sources, as_of):
            if s["document_type"] == "calendar" and s["source_id"] in self.events_by_source:
                return s, self.events_by_source[s["source_id"]]
        return None, []


def find_event(events, code, term_id=None):
    """Return the first event with this code (and term, when given), or None."""
    for e in events:
        if e["code"] == code and (term_id is None or e["term_id"] == term_id):
            return e
    return None


def resolve_term(events, as_of, version, basis="current"):
    """Return the term a question means when it does not name one.

    "current": the term in progress, or the first term before it starts. Used for
    withdrawal and postponement, where "can I still withdraw?" means this term.
    "upcoming": the next term to start. Used for re-enrolment, which is requested
    before a term begins.

    Returns:
        A term id such as "1448-T1", or None when as_of is outside the year.
    """
    if basis == "upcoming":
        for term in (f"{version}-T1", f"{version}-T2"):
            start = find_event(events, "TERM_START", term)
            if start and _date(as_of) < _date(start["date_start"]):
                return term
        return None
    t2 = find_event(events, "TERM_START", f"{version}-T2")
    next_year = find_event(events, "NEXT_YEAR_START")
    day = _date(as_of)
    if t2 and day < _date(t2["date_start"]):
        return f"{version}-T1"
    if t2 and (next_year is None or day < _date(next_year["date_start"])):
        return f"{version}-T2"
    return None
