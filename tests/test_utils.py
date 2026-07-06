"""Unit tests for the pure helpers in app.utils.

Time-dependent logic is pinned to a fixed 'now' (Saturday, 4 July 2026, noon IST)
so assertions are deterministic regardless of when the suite runs.
"""
import datetime as dt
from zoneinfo import ZoneInfo

import pytest

from app import utils

IST = ZoneInfo("Asia/Kolkata")
FIXED_NOW = dt.datetime(2026, 7, 4, 12, 0, tzinfo=IST)  # a Saturday


@pytest.fixture(autouse=True)
def _freeze_now(monkeypatch):
    monkeypatch.setattr(utils, "now_clinic", lambda: FIXED_NOW)


# --- booking reference --------------------------------------------------------
def test_booking_reference_format():
    ref = utils.generate_booking_reference()
    assert ref.startswith("QDC-")
    assert len(ref) == 8  # "QDC-" + 4 chars


# --- relative-day parsing (the bug we fixed) ----------------------------------
def test_tomorrow_resolves_to_next_day_not_today():
    # "tomorrow" from Sat 4 Jul -> Sun 5 Jul, NOT today.
    parsed = utils.parse_datetime("tomorrow at 11am")
    assert parsed is not None
    assert parsed.date() == dt.date(2026, 7, 5)
    assert parsed.hour == 11


def test_day_after_tomorrow():
    parsed = utils.parse_datetime("day after tomorrow at 2pm")
    assert parsed is not None
    assert parsed.date() == dt.date(2026, 7, 6)  # Monday
    assert parsed.hour == 14


def test_next_weekday_still_works():
    parsed = utils.parse_datetime("next Monday at 3pm")
    assert parsed is not None
    assert parsed.weekday() == 0  # Monday
    assert parsed.hour == 15


def test_next_same_weekday_rolls_to_next_week(monkeypatch):
    # Regression: dateutil resolves a bare weekday name to the closest
    # occurrence -- including *today* -- so "next Monday" said on a Monday
    # used to silently resolve to today (often already in the past) instead
    # of a week later.
    monday = dt.datetime(2026, 7, 6, 20, 0, tzinfo=IST)  # a Monday evening
    monkeypatch.setattr(utils, "now_clinic", lambda: monday)

    parsed = utils.parse_datetime("next Monday at 10am")
    assert parsed is not None
    assert parsed.date() == dt.date(2026, 7, 13)  # a week later, not today


def test_bare_time_zeroes_minutes():
    # "3pm" should be 15:00, not 15:<current-minute>.
    parsed = utils.parse_datetime("3pm")
    assert parsed is not None
    assert parsed.minute == 0


def test_unparseable_returns_none():
    assert utils.parse_datetime("") is None
    assert utils.parse_datetime("sometime whenever") is None


def test_spelled_out_hour_does_not_silently_fall_back_to_now(monkeypatch):
    # Regression: dateutil doesn't understand "twelve" (only digits), so it used
    # to silently drop the word and fall back to the current hour. FIXED_NOW is
    # noon, which would coincidentally match the correct answer below and hide
    # a regression -- so freeze "now" to an evening hour instead.
    evening = dt.datetime(2026, 7, 6, 19, 51, tzinfo=IST)
    monkeypatch.setattr(utils, "now_clinic", lambda: evening)

    parsed = utils.parse_datetime("upcoming Thursday for twelve PM")
    assert parsed is not None
    assert parsed.hour == 12
    assert parsed.weekday() == 3  # Thursday

    parsed = utils.parse_datetime("this Wednesday at eleven AM")
    assert parsed is not None
    assert parsed.hour == 11


# --- working-hours checks -----------------------------------------------------
def test_sunday_is_closed():
    sunday = dt.datetime(2026, 7, 5, 11, 0, tzinfo=IST)
    ok, reason = utils.within_working_hours(sunday)
    assert ok is False
    assert "Sunday" in reason


def test_in_hours_weekday_is_open():
    monday = dt.datetime(2026, 7, 6, 15, 0, tzinfo=IST)
    ok, _ = utils.within_working_hours(monday)
    assert ok is True


def test_after_close_is_rejected():
    monday_evening = dt.datetime(2026, 7, 6, 19, 0, tzinfo=IST)
    ok, reason = utils.within_working_hours(monday_evening)
    assert ok is False
    assert "working hours" in reason


def test_past_time_is_rejected():
    earlier_today = dt.datetime(2026, 7, 4, 9, 0, tzinfo=IST)  # 9am, now is noon
    ok, reason = utils.within_working_hours(earlier_today)
    assert ok is False
    assert "past" in reason


# --- formatting (Windows-safe, the other bug we fixed) ------------------------
def test_format_12h_no_leading_zero():
    d = dt.datetime(2026, 7, 6, 9, 0, tzinfo=IST)
    assert utils._format_12h(d, with_minutes=False) == "Monday, July 06 at 9 AM"
    assert utils._format_12h(d, with_minutes=True) == "Monday, July 06 at 9:00 AM"


def test_format_12h_pm():
    d = dt.datetime(2026, 7, 6, 14, 30, tzinfo=IST)
    assert utils._format_12h(d, with_minutes=True) == "Monday, July 06 at 2:30 PM"


def test_suggest_slots_returns_valid_future_slots():
    sunday = dt.datetime(2026, 7, 5, 11, 0, tzinfo=IST)  # closed day
    slots = utils.suggest_slots(sunday)
    assert " or " in slots
    assert "Monday" in slots  # next open day
