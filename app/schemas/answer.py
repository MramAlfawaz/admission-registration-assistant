"""The response schema every answer must satisfy, and its validator."""
import datetime as dt

STATUSES = ("ANSWERABLE", "CLARIFICATION_REQUIRED", "INSUFFICIENT_EVIDENCE",
            "CONFLICTING_EVIDENCE", "OUT_OF_SCOPE", "STAFF_REVIEW_REQUIRED")
FIELDS = ("status", "intent", "language", "as_of", "answer", "conditions", "required_action",
          "rule_outputs", "sources", "date_basis", "clarification", "escalation", "verified")


def validate_response(response):
    """Return a list of schema errors; an empty list means the response is valid.

    Args:
        response: a response dictionary.

    Returns:
        A list of human-readable error strings.
    """
    errors = [f"missing field: {f}" for f in FIELDS if f not in response]
    if errors:
        return errors
    if response["status"] not in STATUSES:
        errors.append(f"unknown status: {response['status']}")
    if response["language"] not in ("ar", "en"):
        errors.append(f"unknown language: {response['language']}")
    try:
        dt.date.fromisoformat(str(response["as_of"]))
    except ValueError:
        errors.append(f"as_of is not a date: {response['as_of']}")
    if not isinstance(response["answer"], str) or not response["answer"].strip():
        errors.append("answer is empty")
    if not isinstance(response["conditions"], list) or not all(isinstance(c, str) for c in response["conditions"]):
        errors.append("conditions must be a list of strings")
    if not isinstance(response["rule_outputs"], list):
        errors.append("rule_outputs must be a list")
    if not isinstance(response["sources"], list):
        errors.append("sources must be a list")
    elif response["status"] == "ANSWERABLE" and not response["sources"]:
        errors.append("ANSWERABLE responses must cite at least one source")
    if not response["date_basis"]:
        errors.append("date_basis is empty")
    return errors
