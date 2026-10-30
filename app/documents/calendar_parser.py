"""Turn extracted academic-calendar text into structured events."""
import datetime as dt
import logging
import re

log = logging.getLogger(__name__)

DATE_LINE = re.compile(
    r"^ه(?P<hy>\d{4})\s*/\s*(?P<hm>\d{2})\s*/\s*(?P<hd>[\d-]+)"
    r"م(?P<gy>\d{4})\s*/\s*(?P<gm>\d{2})\s*/\s*(?P<gd>[\d-]+)$"
)
ROW_START = re.compile(r"^(?P<num>\d+)\s*(?P<text>.*)$")
WEEKDAYS = ["الإثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت", "الأحد"]

EVENT_CODES = [
    ("آخر موعد للاعتذار", "SEMESTER_WITHDRAWAL_DEADLINE"),
    ("آخر موعد لتأجيل", "POSTPONEMENT_DEADLINE"),
    ("آخر موعد لطلب إعادة القيد", "REENROLLMENT_DEADLINE"),
    ("بداية الاختبارات النهائية", "FINAL_EXAMS_START"),
    ("نهاية الاختبارات النهائية", "FINAL_EXAMS_END"),
    ("بداية الدراسة للفصل", "TERM_START"),
    ("بداية الدراسة للعام", "NEXT_YEAR_START"),
    ("بداية الدراسة بعد", "STUDY_RESUMES"),
    ("إجازة", "HOLIDAY"),
    ("يوم التأسيس", "HOLIDAY"),
    ("أعضاء هيئة التدريس", "FACULTY"),
]


def _day_range(part):
    """Return (first, last) day numbers from '19' or a reversed range '24-23'."""
    days = sorted(int(x) for x in part.split("-"))
    return days[0], days[-1]


def _event_code(text):
    """Map an event description to a stable code."""
    for keyword, code in EVENT_CODES:
        if keyword in text:
            return code
    return "OTHER"


def _term_id(text, version):
    """Return the term identifier mentioned in an event, if any."""
    if "فصل الدراسي الأول" in text:
        return f"{version}-T1"
    if "فصل الدراسي الثاني" in text:
        return f"{version}-T2"
    return None


def parse_calendar(text, source_id, version):
    """Parse calendar text into a list of event dictionaries.

    Args:
        text: cleaned text extracted from the calendar PDF.
        source_id: identifier of the calendar source.
        version: calendar version, used to build term identifiers.

    Returns:
        A list of events, each with row, event text, code, term, dates and source.
    """
    events, buffer = [], []
    for line in (ln.strip() for ln in text.splitlines()):
        if not line:
            continue
        m = DATE_LINE.match(line)
        if not m:
            buffer.append(line)
            continue
        starts = [i for i, ln in enumerate(buffer[:-1]) if ROW_START.match(ln)]
        if not starts:
            log.warning("date line without a row: %s", line)
            buffer = []
            continue
        day_text = buffer[-1]
        head = ROW_START.match(buffer[starts[-1]])
        body = " ".join([head["text"]] + buffer[starts[-1] + 1:-1]).strip()
        g_first, g_last = _day_range(m["gd"])
        h_first, h_last = _day_range(m["hd"])
        start = dt.date(int(m["gy"]), int(m["gm"]), g_first)
        end = dt.date(int(m["gy"]), int(m["gm"]), g_last)
        if WEEKDAYS[start.weekday()] not in day_text:
            log.warning("row %s: weekday '%s' does not match %s", head["num"], day_text, start)
        events.append({
            "row": int(head["num"]),
            "event": body,
            "code": _event_code(body),
            "term_id": _term_id(body, version),
            "day": day_text,
            "date_start": start.isoformat(),
            "date_end": end.isoformat(),
            "hijri_start": f"{m['hy']}-{m['hm']}-{h_first:02d}",
            "hijri_end": f"{m['hy']}-{m['hm']}-{h_last:02d}",
            "source_id": source_id,
            "section": f"row {head['num']}",
        })
        buffer = []
    return events
