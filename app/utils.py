"""Small pure helpers: booking references and working-hours checks.

Callers speak dates in free-form natural language ("next Monday at 3pm"), so we
parse leniently with dateutil and fall back gracefully when parsing fails.
"""
from __future__ import annotations

import random
import re
import string
from datetime import datetime, timedelta
from typing import Optional
from zoneinfo import ZoneInfo

from dateutil import parser as dateparser

from .config import settings

WEEKDAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

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


def generate_booking_reference() -> str:
    """Human-friendly reference, e.g. QDC-7F3K."""
    suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"QDC-{suffix}"


def now_clinic() -> datetime:
    return datetime.now(ZoneInfo(settings.CLINIC_TIMEZONE))


def parse_datetime(text: str) -> Optional[datetime]:
    """Best-effort parse of a spoken date/time into a tz-aware datetime.

    Returns None if the text can't be understood at all.
    """
    if not text:
        return None
    tz = ZoneInfo(settings.CLINIC_TIMEZONE)
    try:
        # default fills in parts the caller didn't say (e.g. no year/minute).
        # Zero minutes/seconds so "3pm" -> 3:00, not 3:<current-minute>.
        default = now_clinic().replace(minute=0, second=0, microsecond=0)
        resolved_text = _resolve_relative_days(text, default)
        dt = dateparser.parse(resolved_text, default=default, fuzzy=True)
    except (ValueError, OverflowError, TypeError):
        return None
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=tz)
    return dt


def within_working_hours(dt: datetime) -> tuple[bool, str]:
    """Check a datetime against clinic working hours.

    Returns (ok, reason). `reason` is a short human sentence usable by the agent.
    """
    if dt.weekday() not in settings.OPEN_WEEKDAYS:
        return False, "The clinic is closed on Sundays."
    if dt < now_clinic():
        return False, "That time is in the past."
    if not (settings.OPEN_HOUR <= dt.hour < settings.CLOSE_HOUR):
        return (
            False,
            f"That time is outside our working hours of "
            f"{settings.OPEN_HOUR} AM to {settings.CLOSE_HOUR - 12} PM.",
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


def suggest_slots(dt: Optional[datetime]) -> str:
    """Suggest up to two nearby valid slots as a spoken-friendly string."""
    base = dt or now_clinic()
    suggestions: list[str] = []
    probe = base.replace(minute=0, second=0, microsecond=0)
    guard = 0
    while len(suggestions) < 2 and guard < 60:
        guard += 1
        probe = probe.replace(hour=max(probe.hour, settings.OPEN_HOUR))
        ok, _ = within_working_hours(probe)
        if ok:
            suggestions.append(_format_12h(probe, with_minutes=False))
            probe = probe.replace(hour=probe.hour + 2)
        else:
            # jump to next day's opening hour
            probe = (probe + timedelta(days=1)).replace(
                hour=settings.OPEN_HOUR, minute=0, second=0, microsecond=0
            )
    return " or ".join(suggestions)


def humanize_datetime(dt: Optional[datetime], fallback: str) -> str:
    if dt is None:
        return fallback
    return _format_12h(dt, with_minutes=True)
