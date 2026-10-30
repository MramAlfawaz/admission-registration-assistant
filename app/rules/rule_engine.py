"""Load the rule library and evaluate rules with declared inputs."""
import datetime as dt
import json
from pathlib import Path

from app.rules.calendar_rules import find_event, resolve_term
from app.rules import registration_rules

UNKNOWN = "unknown"


class RuleEngine:
    """Evaluate rules from rules/rule_library.json; every result cites its sources."""

    def __init__(self, library, calendar_store=None):
        self.rules = {r["rule_id"]: r for r in library}
        self.calendar = calendar_store

    @classmethod
    def from_file(cls, path, calendar_store=None):
        """Read the library JSON file."""
        return cls(json.loads(Path(path).read_text(encoding="utf-8")), calendar_store)

    def run(self, rule_id, as_of, **inputs):
        """Evaluate one rule on the query date with the given inputs.

        Args:
            rule_id: identifier from the library.
            as_of: the date the question is about (never read from the clock).
            **inputs: declared inputs, for example term_id or attendance_percent.

        Returns:
            A dict with rule_id, output, details and the rule's sources.
            Missing inputs or data give output "unknown" with a reason.
        """
        rule = self.rules[rule_id]
        result = {"rule_id": rule_id, "sources": rule["sources"], "as_of": str(as_of)}
        day = dt.date.fromisoformat(str(as_of))
        start = dt.date.fromisoformat(rule["effective_from"])
        end = dt.date.fromisoformat(rule["effective_to"]) if rule["effective_to"] else None
        if day < start or (end and day > end):
            return {**result, "output": "not_applicable", "details": {"reason": "rule not in force"}}
        missing = [k for k in rule["inputs"] if k not in ("as_of", "term_id") and inputs.get(k) is None]
        if missing:
            return {**result, "output": UNKNOWN, "details": {"reason": f"missing input: {', '.join(missing)}"}}
        if rule["kind"] == "calendar":
            output, details = self._calendar_rule(rule, day, inputs.get("term_id"))
        else:
            output, details = getattr(registration_rules, rule["function"])(**{k: inputs[k] for k in rule["inputs"]})
        return {**result, "output": output, "details": details}

    def _calendar_rule(self, rule, day, term_id):
        """Compare the query date with a calendar event of the right term."""
        if self.calendar is None:
            return UNKNOWN, {"reason": "no calendar data loaded"}
        source, events = self.calendar.calendar_for(day)
        if source is None:
            return UNKNOWN, {"reason": f"no academic calendar in force on {day}"}
        basis = "stated"
        if term_id is None:
            term_basis = rule.get("term_basis", "current")
            term_id = resolve_term(events, day, source["version"], term_basis)
            basis = f"{term_basis} term resolved from as_of"
        event = find_event(events, rule["event_code"], term_id) if term_id else None
        if event is None:
            return UNKNOWN, {"reason": f"no {rule['event_code']} event for term {term_id}", "term_id": term_id}
        limit = dt.date.fromisoformat(event["date_start"])
        is_open = day <= limit if rule["comparison"] == "on_or_before" else day < limit
        details = {"term_id": term_id, "term_basis": basis, "event": event["event"],
                   "date": event["date_start"], "hijri": event["hijri_start"],
                   "calendar": source["source_id"], "calendar_row": event["row"]}
        return (rule["outputs"][0] if is_open else rule["outputs"][1]), details
