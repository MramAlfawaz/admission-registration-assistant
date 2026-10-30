"""Collect conditions the answer must keep, and detect missing source types."""
import re

from app.documents.normalize import normalize_for_search

CONDITION_MARKERS = ["بشرط", "شريطه", "شرط", "علي ان", "الا اذا", "ما لم", "في حال", "يجوز",
                     "لا يجوز", "لا يحق", "استثناء", "بحد اقصي", "قبل", "خلال", "بعد"]
# Explicit deadline wording; "when" alone can be answered by a rule ("before the first week ends").
DEADLINE_WORDS = ["موعد", "اخر يوم", "deadline", "last day", "date"]
DEADLINE_INTENTS = {"SEMESTER_WITHDRAWAL", "POSTPONEMENT", "REENROLLMENT", "ACADEMIC_CALENDAR"}


def extract_conditions(chunks, limit=3):
    """Return sentences stating conditions or exceptions in the top chunks.

    Args:
        chunks: relevant chunks, best first.
        limit: how many chunks to read.

    Returns:
        A list of {"chunk_id", "text"} items, in reading order.
    """
    conditions = []
    for c in chunks[:limit]:
        for sentence in re.split(r"[.\n؛]", c["text"]):
            s = " ".join(sentence.split())
            if 15 <= len(s) <= 300 and any(m in normalize_for_search(s) for m in CONDITION_MARKERS):
                conditions.append({"chunk_id": c["chunk_id"], "text": s})
    return conditions


def missing_source_types(intent, question, chunks, sources_by_id):
    """Return document types the answer needs but the evidence lacks.

    A deadline question needs the academic calendar in force; without it the
    date cannot be stated, whatever the regulation says.
    """
    asks_deadline = any(w in normalize_for_search(question) for w in DEADLINE_WORDS)
    needs_calendar = intent == "ACADEMIC_CALENDAR" or (intent in DEADLINE_INTENTS and asks_deadline)
    types = {sources_by_id[c["source_id"]]["document_type"] for c in chunks}
    if needs_calendar and "calendar" not in types:
        return ["calendar"]
    return []
