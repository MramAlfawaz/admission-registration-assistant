"""Run the evidence checks in a fixed order before any answer is generated."""
from app.evidence.completeness import extract_conditions, missing_source_types
from app.evidence.contradiction import find_conflicts, resolve
from app.evidence.currency_checker import check_currency
from app.evidence.facts import extract_facts
from app.evidence.relevance import filter_relevant
from app.evidence.subject import compatible, extract_subject

# Fact types that answer each intent; others are ignored for contradiction checks.
FACT_TYPES = {
    "STUDY_DURATION": {"duration"},
    "FEES": {"money"},
    "ATTENDANCE": {"percent"},
    "GRADUATION_REQUIREMENTS": {"gpa"},
    "GRADING_AND_STANDING": {"gpa", "percent"},
    "SEMESTER_WITHDRAWAL": {"date"},
    "POSTPONEMENT": {"date"},
    "REENROLLMENT": {"date"},
    "ACADEMIC_CALENDAR": {"date"},
}


def validate_evidence(intent, question, chunks, sources_by_id, as_of):
    """Check currency, relevance, contradiction and completeness of retrieved evidence.

    Args:
        intent: the classified intent.
        question: the student question.
        chunks: retrieved chunks, best first.
        sources_by_id: source metadata keyed by source_id.
        as_of: the date the question is about.

    Returns:
        A report dict. "status" is "OK", "INSUFFICIENT_EVIDENCE" or
        "CONFLICTING_EVIDENCE"; "evidence" holds the chunks safe to use.
    """
    current, rejected = check_currency(chunks, sources_by_id, as_of)
    relevant, off_topic = filter_relevant(current, intent)

    q_subject = extract_subject(question)
    wanted = FACT_TYPES.get(intent)
    facts = [f for c in relevant for f in extract_facts(c)
             if (wanted is None or f.type in wanted) and compatible(f.subject, q_subject)]
    resolutions = [resolve(c, sources_by_id) for c in find_conflicts(facts)]
    unresolved = [r for r in resolutions if r["winner"] is None]

    overridden = {r["chunks"][s] for r in resolutions if r["winner"] for s in r["flag_for_review"]}
    evidence = [c for c in relevant if c["chunk_id"] not in overridden]
    missing = missing_source_types(intent, question, evidence, sources_by_id)

    if unresolved:
        status = "CONFLICTING_EVIDENCE"
    elif not evidence or missing:
        status = "INSUFFICIENT_EVIDENCE"
    else:
        status = "OK"
    return {
        "status": status,
        "evidence": evidence,
        "rejected_not_current": rejected,
        "off_topic": off_topic,
        "conflicts": resolutions,
        "overridden_chunks": sorted(overridden),
        "conditions": extract_conditions(evidence),
        "missing_source_types": missing,
    }
