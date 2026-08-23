"""Shared accessible OAP status-light language.

This is presentation vocabulary, not another OAP Signal system.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

LIGHT_SIGNALS: tuple[dict[str, str], ...] = (
    {"id": "healthy", "emoji": "🟢", "label": "Live / Healthy", "colour": "green"},
    {"id": "review", "emoji": "🟡", "label": "Review Required", "colour": "yellow"},
    {"id": "degraded", "emoji": "🟠", "label": "Degraded / Partially working", "colour": "orange"},
    {"id": "blocked", "emoji": "🔴", "label": "Blocked / Critical", "colour": "red"},
    {"id": "learning", "emoji": "🟣", "label": "Learning / Processing", "colour": "purple"},
    {"id": "information", "emoji": "🔵", "label": "Information / Verified update", "colour": "blue"},
    {"id": "not_connected", "emoji": "⚪", "label": "Not Connected", "colour": "white"},
    {"id": "disabled", "emoji": "⚫", "label": "Offline / Disabled", "colour": "black"},
)

EVENT_SIGNALS: tuple[dict[str, str], ...] = (
    {"id": "approved", "emoji": "✅", "label": "Human Approved"},
    {"id": "rejected", "emoji": "❌", "label": "Human Rejected"},
    {"id": "protected", "emoji": "🔒", "label": "Protected / Permission Required"},
    {"id": "smi_learning", "emoji": "🧠🟣", "label": "SMI Learning"},
    {"id": "agent_learning", "emoji": "🤖🟣", "label": "Agent Learning"},
    {"id": "hrm_learning", "emoji": "💾🟣", "label": "HRM Recording a Lesson"},
    {"id": "earth_learning", "emoji": "🌍🟣", "label": "Earth Intelligence Researching"},
    {"id": "signal_received", "emoji": "📡", "label": "New Signal Received"},
    {"id": "approved_work", "emoji": "⚡", "label": "Approved Work in Progress"},
)


def validate_light_signals(
    signals: Iterable[Mapping[str, Any]] = LIGHT_SIGNALS,
) -> dict[str, Any]:
    """Reject duplicate meanings and protect purple as the learning colour."""

    items = tuple(signals)
    ids = [str(item.get("id", "")) for item in items]
    colours = [str(item.get("colour", "")) for item in items]
    errors: list[str] = []
    if len(ids) != len(set(ids)):
        errors.append("Duplicate light-signal IDs")
    if len(colours) != len(set(colours)):
        errors.append("Duplicate light-signal colours")
    learning = next((item for item in items if item.get("id") == "learning"), {})
    if learning.get("colour") != "purple" or learning.get("emoji") != "🟣":
        errors.append("Learning must remain purple")
    return {
        "passed": not errors,
        "errors": errors,
        "checks": {"signals": len(items), "purple_learning_locked": not errors},
    }


def get_public_light_signals() -> dict[str, Any]:
    """Return text-labelled status signals for accessible rendering."""

    return {
        "lights": tuple(dict(item) for item in LIGHT_SIGNALS),
        "events": tuple(dict(item) for item in EVENT_SIGNALS),
        "validation": validate_light_signals(),
        "boundary": "Visual status language only — not a duplicate OAP Signal system",
    }
