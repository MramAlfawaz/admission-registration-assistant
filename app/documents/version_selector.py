"""Decide which document versions were in force on a given date."""
import datetime as dt


def _to_date(value):
    """Convert an ISO string or date to a date, keeping None."""
    if value is None or isinstance(value, dt.date):
        return value
    return dt.date.fromisoformat(value)


def in_force(source, as_of):
    """Return True when the source applies on the given date.

    A missing effective_from means the start date is unknown and the source
    is treated as in force; effective_to is inclusive.

    Args:
        source: a source metadata dictionary.
        as_of: the date the question is about, as a date or ISO string.

    Returns:
        True if as_of falls inside the effective period.
    """
    day = _to_date(as_of)
    start = _to_date(source.get("effective_from"))
    end = _to_date(source.get("effective_to"))
    if start and day < start:
        return False
    if end and day > end:
        return False
    return True


def select_sources(sources, as_of):
    """Return the sources in force on a date, never by newest version.

    Args:
        sources: list of source metadata dictionaries.
        as_of: the date the question is about.

    Returns:
        The subset of sources in force on that date, in the original order.
    """
    return [s for s in sources if in_force(s, as_of)]


def current_version(sources, family, as_of):
    """Return the single source of a document family in force on a date.

    Args:
        sources: list of source metadata dictionaries.
        family: source_id prefix, for example "CALENDAR" or "PROGRAMS-GUIDE".
        as_of: the date the question is about.

    Returns:
        The matching source dictionary, or None when no version applies.

    Raises:
        ValueError: if two versions of the family overlap on that date.
    """
    matches = [s for s in select_sources(sources, as_of)
               if s["source_id"].startswith(family + "-")]
    if len(matches) > 1:
        ids = ", ".join(s["source_id"] for s in matches)
        raise ValueError(f"overlapping versions of {family} on {as_of}: {ids}")
    return matches[0] if matches else None
