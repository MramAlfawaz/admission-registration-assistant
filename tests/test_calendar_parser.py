import datetime as dt
from pathlib import Path

from app.documents.calendar_parser import parse_calendar

TEXT = (Path(__file__).parent / "fixtures" / "calendar_1448.txt").read_text(encoding="utf-8")
EVENTS = parse_calendar(TEXT, "CALENDAR-1448", "1448")
BY_ROW = {e["row"]: e for e in EVENTS}


def test_all_rows_parsed():
    assert [e["row"] for e in EVENTS] == list(range(1, 25))


def test_first_term_withdrawal_deadline():
    e = BY_ROW[6]
    assert e["code"] == "SEMESTER_WITHDRAWAL_DEADLINE"
    assert e["term_id"] == "1448-T1"
    assert e["date_start"] == "2026-11-19"
    assert e["event"] == "آخر موعد للاعتذار عن الفصل الدراسي الأول"


def test_row_number_on_its_own_line():
    assert BY_ROW[2]["event"] == "آخر موعد لطلب إعادة القيد للفصل الدراسي الأول"
    assert BY_ROW[2]["code"] == "REENROLLMENT_DEADLINE"


def test_reversed_day_range():
    assert (BY_ROW[5]["date_start"], BY_ROW[5]["date_end"]) == ("2026-09-23", "2026-09-24")
    assert (BY_ROW[14]["hijri_start"], BY_ROW[14]["hijri_end"]) == ("1448-09-14", "1448-09-15")


def test_second_term_events():
    assert BY_ROW[11]["code"] == "TERM_START" and BY_ROW[11]["date_start"] == "2027-01-03"
    assert BY_ROW[18]["term_id"] == "1448-T2" and BY_ROW[18]["date_start"] == "2027-05-24"


def test_hijri_year_change():
    assert BY_ROW[19]["hijri_start"] == "1449-01-01"


def test_term_ids_with_lil_prefix():
    assert BY_ROW[3]["term_id"] == "1448-T1"
    assert BY_ROW[7]["term_id"] == "1448-T1"
    assert BY_ROW[11]["term_id"] == "1448-T2"


def test_weekdays_match_dates():
    names = ["الإثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت", "الأحد"]
    for e in EVENTS:
        assert names[dt.date.fromisoformat(e["date_start"]).weekday()] in e["day"]
