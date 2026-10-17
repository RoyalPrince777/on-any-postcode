"""Read-only OAP calendar labels and evidence provenance boundary.

No historical epoch, date conversion, or production route is claimed.
"""
from __future__ import annotations

from datetime import date
from typing import Mapping

OAP_WEEKDAYS = (
    "Mission Day", "Power Day", "Wisdom Day", "Royal Day",
    "Freedom Day", "Legacy Day", "Recharge Day",
)
AKAN_WEEKDAYS = (
    "Dwoada", "Benada", "Wukuada", "Yawoada",
    "Fida", "Memeneda", "Kwasiada",
)
EVIDENCE_KINDS = frozenset({"scientific", "historical", "religious_tradition", "oap_creation"})


def calendar_labels(day: date) -> dict[str, str]:
    """Return civil-compatible labels; only August has an approved OAP month name."""
    if not isinstance(day, date):
        raise TypeError("day must be a datetime.date")
    index = day.weekday()
    return {
        "iso_date": day.isoformat(),
        "civil_weekday": day.strftime("%A"),
        "civil_month": day.strftime("%B"),
        "oap_weekday": OAP_WEEKDAYS[index],
        "akan_weekday": AKAN_WEEKDAYS[index],
        "oap_month": "AUGUSTINE" if day.month == 8 else day.strftime("%B"),
        "oap_week": "STRONG 7",
    }


def validate_evidence_record(record: Mapping[str, object]) -> bool:
    """Fail closed for missing provenance and unsupported classification."""
    if not isinstance(record, Mapping):
        return False
    if record.get("kind") not in EVIDENCE_KINDS:
        return False
    for key in ("claim", "source", "uncertainty"):
        value = record.get(key)
        if not isinstance(value, str) or not value.strip():
            return False
    return True
