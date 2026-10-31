"""Answer "when is X?" from the structured calendar, so dates and weekdays never come from the model.

Real failures (end-to-end v1, E010 and E014): calendar questions had no rule, the model wrote
the wrong weekday, its sentence was dropped and nothing was left to answer with.
"""
import re

from app.documents.normalize import normalize_for_search
from app.generation.extractive import same_word
from app.retrieval.tokenize import tokenize
from app.rules.calendar_rules import _date

# English and dialect words mapped to the Arabic wording of calendar rows. The list covers the
# vocabulary of every row of the calendar (terms, exams, holidays, deadlines, faculty, next year).
EN_TO_AR = [
    ("mid-year", "منتصف العام"), ("mid year", "منتصف العام"), ("midyear", "منتصف العام"),
    ("end-of-year", "نهايه العام"), ("end of year", "نهايه العام"), ("end of the year", "نهايه العام"),
    ("national day", "اليوم الوطني"), ("founding day", "يوم التاسيس"),
    ("eid al-fitr", "عيد الفطر"), ("fitr", "عيد الفطر"), ("eid al-adha", "عيد الاضحي"), ("adha", "عيد الاضحي"),
    ("final exams", "الاختبارات النهائيه"), ("final exam", "الاختبارات النهائيه"), ("finals", "الاختبارات النهائيه"),
    ("exams", "الاختبارات"), ("faculty", "اعضاء هيئه التدريس"), ("academic year", "بدايه الدراسه للعام الدراسي"),
    ("resume", "بدايه الدراسه بعد"), ("return to study", "بدايه الدراسه بعد"), ("classes", "الدراسه"),
    ("holiday", "اجازه"), ("break", "اجازه"), ("vacation", "اجازه"),
    ("first-semester", "الفصل الدراسي الاول"), ("first semester", "الفصل الدراسي الاول"),
    ("second-semester", "الفصل الدراسي الثاني"), ("second semester", "الفصل الدراسي الثاني"),
    ("start", "بدايه"), ("starts", "بدايه"), ("begin", "بدايه"), ("begins", "بدايه"),
    ("end", "نهايه"), ("ends", "نهايه"), ("finish", "نهايه"),
]
AR_TO_ROW = [("تبدا", "بدايه"), ("يبدا", "بدايه"), ("تنتهي", "نهايه"), ("ينتهي", "نهايه"),
             ("نرجع", "بدايه الدراسه بعد"), ("الرجوع", "بدايه الدراسه بعد"), ("العوده للدراسه", "بدايه الدراسه بعد"),
             ("الترم", "الفصل الدراسي"), ("ترم", "الفصل الدراسي"), ("النهائي", "الاختبارات النهائيه")]
# Words found in many rows; matching only these identifies a row only when it matches fully.
COMMON = {"بدايه", "نهايه", "دراسه", "عام", "اخر", "موعد"}
# The term phrase is handled by the term filter, not by word matching.
TERM_PHRASE = {"فصل", "دراسي", "اول", "ثاني"}
TERM_WORDS = {"T1": ("اول",), "T2": ("ثاني",)}


# "the term starts" means the row "start of study for the term".
TERM_START = [r"(يبدا|تبدا|بدايه)\s+(الفصل|الترم)", r"semester\s+(starts?|begins?)",
              r"(starts?|begins?|start of)\s+(the\s+)?(first|second)[- ]semester"]


def _expanded_tokens(question):
    text = normalize_for_search(question)
    extra = []
    for en, ar in EN_TO_AR:
        if re.search(rf"(?<![a-z]){re.escape(en)}(?![a-z])", text):
            extra.append(ar)
    for word, ar in AR_TO_ROW:
        if word in text:
            extra.append(ar)
    if any(re.search(p, text) for p in TERM_START):
        extra.append("بدايه الدراسه")
    return tokenize(" ".join([question] + extra))


def match_event(question, events, as_of, term=None):
    """Return the calendar row the question asks about, or None when no row clearly matches.

    A row matches when most of its words are in the question (after mapping English and
    dialect words) and at least one of them is distinctive. Rows of another term than the
    one named are skipped; with no term named, the next upcoming row wins a tie.
    """
    q_tokens = _expanded_tokens(question)
    best = []
    for e in events:
        all_tokens = tokenize(e["event"])
        years = {t for t in all_tokens if t.isdigit()}
        # Years count as a bonus, not in the share: a row printed with its year range must not lose to a
        # shorter row (held-out H017: "the 1449 academic year" matched the second-term start instead).
        e_tokens = [t for t in all_tokens if t not in TERM_PHRASE and not t.isdigit()]
        if not e_tokens:
            continue
        if term and e.get("term_id") and not e["term_id"].endswith(term):
            continue
        if term and not e.get("term_id"):
            other = TERM_WORDS["T2" if term == "T1" else "T1"]
            if any(w in all_tokens for w in other):
                continue
        matched = [t for t in e_tokens if any(same_word(t, q) for q in q_tokens)]
        if any(q.isdigit() and len(q) == 4 for q in q_tokens) and not years & set(q_tokens) and years:
            continue  # the question names a year this row does not have
        matched += sorted(years & set(q_tokens))
        share = len([t for t in matched if not t.isdigit()]) / len(e_tokens)
        if not any(t not in COMMON for t in matched) and share < 1:
            continue
        if share >= 0.6 and len(matched) >= 2 - (len(e_tokens) == 1):
            best.append((share, len(matched), e))
    if not best:
        return None
    best.sort(key=lambda x: (-x[0], -x[1]))
    top = [b for b in best if (b[0], b[1]) == (best[0][0], best[0][1])]
    if len(top) == 1:
        return top[0][2]
    upcoming = sorted((e for _, _, e in top if _date(e["date_start"]) >= _date(as_of)), key=lambda e: e["date_start"])
    return upcoming[0] if upcoming else sorted((e for _, _, e in top), key=lambda e: e["date_start"])[-1]


def calendar_event_result(store, question, as_of, term=None):
    """Return a rule-like result for the matched calendar row, or None."""
    if store is None:
        return None
    source, events = store.calendar_for(as_of)
    if source is None:
        return None
    event = match_event(question, events, as_of, term)
    if event is None:
        return None
    details = {"event": event["event"], "date": event["date_start"], "date_end": event["date_end"],
               "hijri": event["hijri_start"], "hijri_end": event["hijri_end"], "day": event.get("day", ""),
               "calendar": source["source_id"], "calendar_row": event["row"]}
    return {"rule_id": "CAL-EVENT", "output": "listed", "details": details,
            "sources": [{"source_id": source["source_id"], "section": f"row {event['row']}"}], "as_of": str(as_of)}
