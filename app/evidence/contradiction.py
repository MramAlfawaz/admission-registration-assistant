"""Find disagreeing facts between sources and resolve them by the authority hierarchy."""
import datetime as dt

from app.evidence.facts import same_value
from app.evidence.subject import compatible

COMPARABLE_KINDS = {"unknown", "other"}


def find_conflicts(facts):
    """Group facts that describe the same thing but state different values.

    Two facts conflict when they have the same type and kind, compatible
    subjects, come from different sources, and their values differ.

    Args:
        facts: Fact objects that apply to the question.

    Returns:
        A list of conflicts; each is a list of the disagreeing facts.
    """
    usable, keys = [], set()
    for f in facts:
        key = (f.type, f.kind, str(f.value), f.source_id, tuple(sorted(f.subject.items())))
        if f.kind not in COMPARABLE_KINDS and key not in keys:
            keys.add(key)
            usable.append(f)
    conflicts, seen = [], set()
    for i, a in enumerate(usable):
        if i in seen:
            continue
        group = [a]
        for j in range(i + 1, len(usable)):
            b = usable[j]
            if (b.type == a.type and b.kind == a.kind and compatible(a.subject, b.subject)
                    and b.source_id != a.source_id and not same_value(a.value, b.value)
                    and all(not (g.source_id == b.source_id and same_value(g.value, b.value)) for g in group)):
                group.append(b)
                seen.add(j)
        if len({f.source_id for f in group}) > 1:
            conflicts.append(group)
    return conflicts


def _rank_key(source):
    """Lower is stronger: approved before superseded, lower authority level, later start."""
    start = source.get("effective_from")
    ordinal = dt.date.fromisoformat(start).toordinal() if start else 0
    return (0 if source.get("status") == "approved" else 1, source.get("authority_level", 99), -ordinal)


RULES = ("status", "authority", "effective_date")


def resolve(conflict, sources_by_id):
    """Pick the applicable value by status, then authority, then effective date.

    Args:
        conflict: disagreeing facts from find_conflicts.
        sources_by_id: source metadata keyed by source_id.

    Returns:
        A dict with the values per source, the winner (None if unresolved),
        the deciding rule, and the sources to flag for department review.
    """
    by_source = {}
    for f in conflict:
        by_source.setdefault(f.source_id, f)
    ranked = sorted(by_source, key=lambda s: _rank_key(sources_by_id[s]))
    best, runner = ranked[0], ranked[1]
    kb, kr = _rank_key(sources_by_id[best]), _rank_key(sources_by_id[runner])
    first = conflict[0]
    record = {"type": first.type, "kind": first.kind, "subject": first.subject,
              "values": {s: by_source[s].value for s in ranked},
              "chunks": {s: by_source[s].chunk_id for s in ranked}}
    if kb == kr:
        return {**record, "winner": None, "rule": "unresolved", "flag_for_review": ranked}
    rule = RULES[next(i for i in range(3) if kb[i] != kr[i])]
    return {**record, "winner": best, "rule": rule, "flag_for_review": ranked[1:]}
