"""First-party Born Day weekday calculation; no identity or gameplay authority.

A full date of birth is optional: callers may supply a weekday directly.
The engine never persists or publishes a date of birth.
"""
from __future__ import annotations

from datetime import date

WEEKDAYS = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")
AKAN_DAY_NAMES = {
    "Monday": {"male": "Kwadwo", "female": "Adwoa"},
    "Tuesday": {"male": "Kwabena", "female": "Abena"},
    "Wednesday": {"male": "Kwaku", "female": "Akua"},
    "Thursday": {"male": "Yaw", "female": "Yaa"},
    "Friday": {"male": "Kofi", "female": "Afua"},
    "Saturday": {"male": "Kwame", "female": "Ama"},
    "Sunday": {"male": "Kwasi", "female": "Akosua"},
}


def weekday_from_date(iso_date: str) -> str:
    """Return weekday for a strict ISO YYYY-MM-DD calendar date.

    No timezone conversion is performed: a birth *calendar date* is not an instant.
    """
    if not isinstance(iso_date, str) or len(iso_date) != 10:
        raise ValueError("born_day_invalid_date")
    try:
        parsed = date.fromisoformat(iso_date)
    except (TypeError, ValueError) as exc:
        raise ValueError("born_day_invalid_date") from exc
    if parsed.isoformat() != iso_date:
        raise ValueError("born_day_invalid_date")
    return WEEKDAYS[parsed.weekday()]


def choose_weekday(*, weekday: str | None = None, birth_date: str | None = None) -> str:
    """Prefer a user-chosen weekday; reject contradictory inputs."""
    chosen = weekday.strip().title() if isinstance(weekday, str) else None
    if chosen is not None and chosen not in WEEKDAYS:
        raise ValueError("born_day_invalid_weekday")
    calculated = weekday_from_date(birth_date) if birth_date is not None else None
    if chosen and calculated and chosen != calculated:
        raise ValueError("born_day_weekday_mismatch")
    if not chosen and not calculated:
        raise ValueError("born_day_weekday_required")
    return chosen or calculated


def akan_name(weekday: str, gender: str) -> str:
    """Optional cultural lookup; never infer gender or identity."""
    if weekday not in AKAN_DAY_NAMES or gender not in ("male", "female"):
        raise ValueError("born_day_akan_name_invalid")
    return AKAN_DAY_NAMES[weekday][gender]
