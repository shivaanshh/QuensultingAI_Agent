"""Small pure helpers: booking references and working-hours checks.

Callers speak dates in free-form natural language ("next Monday at 3pm"), so we
parse leniently with dateutil and fall back gracefully when parsing fails.

Every function takes the tenant's timezone/hours/weekdays/prefix as explicit
parameters (defaulting to today's dental values) instead of reading a global
settings singleton -- required so concurrent requests for different tenants
never leak one tenant's hours into another's response.
"""
from __future__ import annotations

import random
import re
import string
from datetime import datetime, timedelta
from typing import Optional, Sequence
from zoneinfo import ZoneInfo

from dateutil import parser as dateparser

WEEKDAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

DEFAULT_TIMEZONE = "Asia/Kolkata"
DEFAULT_OPEN_HOUR = 9
DEFAULT_CLOSE_HOUR = 18
DEFAULT_OPEN_WEEKDAYS: tuple[int, ...] = (0, 1, 2, 3, 4, 5)  # Mon-Sat
DEFAULT_BOOKING_PREFIX = "QDC"

# dateutil has no concept of relative-day words: it silently drops any word it
# doesn't recognize (fuzzy parsing), so "tomorrow at 8pm" quietly becomes
# "today at 8pm" instead of erroring. Rewrite the common phrases to an
# explicit date dateutil *does* understand before parsing. Longest phrases
# first so "day after tomorrow" isn't shadowed by the "tomorrow" pattern.
_RELATIVE_DAY_OFFSETS = [
    (re.compile(r"\bday after tomorrow\b", re.IGNORECASE), 2),
    (re.compile(r"\btomorrow\b", re.IGNORECASE), 1),
    (re.compile(r"\btoday\b", re.IGNORECASE), 0),
    (re.compile(r"\btonight\b", re.IGNORECASE), 0),
]


def _resolve_relative_days(text: str, reference: datetime) -> str:
    """Replace relative-day words with an explicit 'Month DD YYYY' date."""
    for pattern, offset_days in _RELATIVE_DAY_OFFSETS:
        if pattern.search(text):
            target = reference + timedelta(days=offset_days)
            return pattern.sub(target.strftime("%B %d %Y"), text)
    return text


# dateutil only recognizes digit hours ("12 PM"), not spelled-out ones
# ("twelve PM") -- it silently drops the unrecognized word (fuzzy parsing)
# and falls back to the current hour, so a caller saying "twelve PM" can
# silently become "whatever hour it is right now, PM". Rewrite spoken
# numbers to digits before parsing.
_NUMBER_WORDS = {
    "one": "1", "two": "2", "three": "3", "four": "4", "five": "5",
    "six": "6", "seven": "7", "eight": "8", "nine": "9", "ten": "10",
    "eleven": "11", "twelve": "12",
}
_WORD_NUMBER_RE = re.compile(r"\b(" + "|".join(_NUMBER_WORDS) + r")\b", re.IGNORECASE)


def _resolve_word_numbers(text: str) -> str:
    """Replace spoken hour words/'noon'/'midnight' with digits dateutil understands."""
    text = re.sub(r"\bnoon\b", "12 PM", text, flags=re.IGNORECASE)
    text = re.sub(r"\bmidnight\b", "12 AM", text, flags=re.IGNORECASE)
    return _WORD_NUMBER_RE.sub(lambda m: _NUMBER_WORDS[m.group(1).lower()], text)


_WEEKDAY_INDEX = {name.lower(): i for i, name in enumerate(WEEKDAY_NAMES)}
_NEXT_WEEKDAY_RE = re.compile(r"\bnext\s+(" + "|".join(_WEEKDAY_INDEX) + r")\b", re.IGNORECASE)


def _resolve_next_weekday(text: str, reference: datetime) -> str:
    """"next Monday" said on a Monday means next week, not today -- dateutil
    resolves a bare weekday name to the closest occurrence (today included),
    so force it a week forward when the caller explicitly says "next" and
    today already is that weekday.
    """
    match = _NEXT_WEEKDAY_RE.search(text)
    if match and _WEEKDAY_INDEX[match.group(1).lower()] == reference.weekday():
        target = reference + timedelta(days=7)
        return _NEXT_WEEKDAY_RE.sub(target.strftime("%B %d %Y"), text, count=1)
    return text


def generate_booking_reference(prefix: str = DEFAULT_BOOKING_PREFIX) -> str:
    """Human-friendly reference, e.g. QDC-7F3K."""
    suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"{prefix}-{suffix}"


def now_clinic(tz: str = DEFAULT_TIMEZONE) -> datetime:
    return datetime.now(ZoneInfo(tz))


def parse_datetime(text: str, tz: str = DEFAULT_TIMEZONE) -> Optional[datetime]:
    """Best-effort parse of a spoken date/time into a tz-aware datetime.

    Returns None if the text can't be understood at all.
    """
    if not text:
        return None
    zone = ZoneInfo(tz)
    try:
        # default fills in parts the caller didn't say (e.g. no year/minute).
        # Zero minutes/seconds so "3pm" -> 3:00, not 3:<current-minute>.
        default = now_clinic(tz).replace(minute=0, second=0, microsecond=0)
        resolved_text = _resolve_relative_days(text, default)
        resolved_text = _resolve_word_numbers(resolved_text)
        resolved_text = _resolve_next_weekday(resolved_text, default)
        dt = dateparser.parse(resolved_text, default=default, fuzzy=True)
    except (ValueError, OverflowError, TypeError):
        return None
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=zone)
    return dt


def within_working_hours(
    dt: datetime,
    open_hour: int = DEFAULT_OPEN_HOUR,
    close_hour: int = DEFAULT_CLOSE_HOUR,
    open_weekdays: Sequence[int] = DEFAULT_OPEN_WEEKDAYS,
    tz: str = DEFAULT_TIMEZONE,
) -> tuple[bool, str]:
    """Check a datetime against a tenant's working hours.

    Returns (ok, reason). `reason` is a short human sentence usable by the agent.
    """
    if dt.weekday() not in open_weekdays:
        return False, f"We're closed on {WEEKDAY_NAMES[dt.weekday()]}s."
    if dt < now_clinic(tz):
        return False, "That time is in the past."
    if not (open_hour <= dt.hour < close_hour):
        return (
            False,
            f"That time is outside our working hours of "
            f"{open_hour} AM to {close_hour - 12} PM.",
        )
    return True, "The requested slot is within working hours."


def _format_12h(dt: datetime, with_minutes: bool) -> str:
    """Format a datetime as e.g. 'Monday, July 06 at 3:00 PM'.

    `%-I` (no leading zero) is Unix-only and raises ValueError on Windows,
    which uses `%#I` instead — so format with `%I` and strip the zero-pad.
    """
    pattern = "%A, %B %d at %I:%M %p" if with_minutes else "%A, %B %d at %I %p"
    text = dt.strftime(pattern)
    hour_str, rest = text.split(" at ", 1)
    if rest[0] == "0":
        rest = rest[1:]
    return f"{hour_str} at {rest}"


def suggest_slots(
    dt: Optional[datetime],
    open_hour: int = DEFAULT_OPEN_HOUR,
    close_hour: int = DEFAULT_CLOSE_HOUR,
    open_weekdays: Sequence[int] = DEFAULT_OPEN_WEEKDAYS,
    tz: str = DEFAULT_TIMEZONE,
) -> str:
    """Suggest up to two nearby valid slots as a spoken-friendly string."""
    base = dt or now_clinic(tz)
    suggestions: list[str] = []
    probe = base.replace(minute=0, second=0, microsecond=0)
    guard = 0
    while len(suggestions) < 2 and guard < 60:
        guard += 1
        probe = probe.replace(hour=max(probe.hour, open_hour))
        ok, _ = within_working_hours(probe, open_hour, close_hour, open_weekdays, tz)
        if ok:
            suggestions.append(_format_12h(probe, with_minutes=False))
            probe = probe.replace(hour=probe.hour + 2)
        else:
            # jump to next day's opening hour
            probe = (probe + timedelta(days=1)).replace(
                hour=open_hour, minute=0, second=0, microsecond=0
            )
    return " or ".join(suggestions)


def humanize_datetime(dt: Optional[datetime], fallback: str) -> str:
    if dt is None:
        return fallback
    return _format_12h(dt, with_minutes=True)
