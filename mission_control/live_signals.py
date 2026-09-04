"""Canonical first-party OAP live signal language.

The signal language is owned by ON ANY POSTCODE. It provides one machine-readable
state vocabulary for OAP interfaces, War Room projections and intelligence
status. It does not probe networks, infer success, approve actions or grant
authority. Purple is reserved for Learning and is never a warning/verdict colour.
"""

from __future__ import annotations

from typing import Any

LIVE_SIGNALS: tuple[dict[str, str], ...] = (
    {"id": "healthy", "emoji": "🟢", "label": "Healthy", "group": "health", "meaning": "Healthy and safe to proceed within the stated boundary."},
    {"id": "starting", "emoji": "🔵", "label": "Starting", "group": "activity", "meaning": "Starting or warming up; readiness is not yet complete."},
    {"id": "warning", "emoji": "🟡", "label": "Warning", "group": "health", "meaning": "Attention required; keep review open until evidence closes the gap."},
    {"id": "busy", "emoji": "🟠", "label": "Busy", "group": "activity", "meaning": "Actively occupied or under elevated workload."},
    {"id": "critical", "emoji": "🔴", "label": "Critical", "group": "health", "meaning": "Critical condition; fail closed or stop consequential progression."},
    {"id": "offline", "emoji": "⚪", "label": "Offline", "group": "system", "meaning": "Unavailable or not connected."},
    {"id": "learning", "emoji": "🟣", "label": "Learning", "group": "cognition", "meaning": "Learning or adapting from evidence. Purple is not a warning signal."},
    {"id": "maintenance", "emoji": "🟤", "label": "Maintenance", "group": "state", "meaning": "Planned maintenance or bounded upkeep."},
    {"id": "high_performance", "emoji": "⚡", "label": "High Performance", "group": "system", "meaning": "Measured high-performance operating state."},
    {"id": "connected", "emoji": "📡", "label": "Connected", "group": "system", "meaning": "A connection is currently evidenced."},
    {"id": "synchronising", "emoji": "🔄", "label": "Synchronising", "group": "cognition", "meaning": "State or evidence is synchronising."},
    {"id": "memory_active", "emoji": "💾", "label": "Memory Active", "group": "system", "meaning": "Memory or audited state handling is active."},
    {"id": "thinking", "emoji": "🧠", "label": "Thinking", "group": "cognition", "meaning": "Reasoning or analysis is active."},
    {"id": "mind_healthy", "emoji": "❤️", "label": "Mind Healthy", "group": "health", "meaning": "Mind-layer health is reported healthy."},
    {"id": "body_healthy", "emoji": "💪", "label": "Body Healthy", "group": "health", "meaning": "Body/execution-layer health is reported healthy."},
    {"id": "soul_healthy", "emoji": "✨", "label": "Soul Healthy", "group": "health", "meaning": "Soul/purpose-and-values layer is aligned and healthy."},
    {"id": "protected", "emoji": "🛡", "label": "Protected", "group": "state", "meaning": "A protection boundary is active."},
    {"id": "improving", "emoji": "📈", "label": "Improving", "group": "state", "meaning": "Measured improvement is underway."},
    {"id": "alert", "emoji": "🚨", "label": "Alert", "group": "state", "meaning": "An alert requires attention or review."},
    {"id": "complete", "emoji": "✅", "label": "Complete", "group": "state", "meaning": "The stated bounded task or gate is complete."},
    {"id": "working", "emoji": "⏳", "label": "Working", "group": "activity", "meaning": "Work is actively in progress."},
    {"id": "idle", "emoji": "💤", "label": "Idle", "group": "activity", "meaning": "Available but not currently active."},
)

SIGNAL_GROUPS: tuple[dict[str, Any], ...] = (
    {"id": "health", "name": "Health", "signals": ("healthy", "warning", "critical", "mind_healthy", "body_healthy", "soul_healthy")},
    {"id": "activity", "name": "Activity", "signals": ("busy", "starting", "working", "idle")},
    {"id": "cognition", "name": "Cognition", "signals": ("thinking", "learning", "synchronising")},
    {"id": "system", "name": "System", "signals": ("connected", "high_performance", "memory_active", "offline")},
    {"id": "state", "name": "State", "signals": ("protected", "improving", "alert", "complete", "maintenance")},
)

MIND_BODY_SOUL_SIGNALS: dict[str, tuple[dict[str, str], ...]] = {
    "mind": (
        {"emoji": "🧠", "label": "Thinking", "meaning": "Reasoning"},
        {"emoji": "📚", "label": "Learning", "meaning": "Learning"},
        {"emoji": "🔍", "label": "Analysing", "meaning": "Analysis"},
        {"emoji": "🎯", "label": "Planning", "meaning": "Planning"},
        {"emoji": "💡", "label": "Ideas", "meaning": "Ideas"},
        {"emoji": "📖", "label": "Knowledge", "meaning": "Knowledge"},
    ),
    "body": (
        {"emoji": "⚙", "label": "Executing", "meaning": "Bounded execution state"},
        {"emoji": "📡", "label": "Sending", "meaning": "Sending"},
        {"emoji": "📥", "label": "Receiving", "meaning": "Receiving"},
        {"emoji": "🔄", "label": "Processing", "meaning": "Processing"},
        {"emoji": "🏃", "label": "Working", "meaning": "Working"},
        {"emoji": "🛠", "label": "Building", "meaning": "Building"},
    ),
    "soul": (
        {"emoji": "❤️", "label": "Ethics", "meaning": "Ethics"},
        {"emoji": "⚖", "label": "Governance", "meaning": "Governance"},
        {"emoji": "🛡", "label": "Safety", "meaning": "Safety"},
        {"emoji": "🤝", "label": "Community", "meaning": "Community"},
        {"emoji": "🌍", "label": "Human / World Alignment", "meaning": "Human and world alignment"},
    ),
}

ALIASES = {
    "ready": "healthy",
    "live": "healthy",
    "ok": "healthy",
    "degraded": "warning",
    "pending": "warning",
    "configured": "warning",
    "amber": "warning",
    "yellow": "warning",
    "in_progress": "working",
    "processing": "working",
    "sync": "synchronising",
    "syncing": "synchronising",
    "synchronizing": "synchronising",
    "not_connected": "offline",
    "unavailable": "offline",
    "failed": "critical",
    "error": "critical",
    "blocked": "critical",
    "certified": "complete",
}


def _by_id() -> dict[str, dict[str, str]]:
    return {item["id"]: dict(item) for item in LIVE_SIGNALS}


def get_signal(signal_id: object) -> dict[str, str]:
    """Return one canonical signal, defaulting safely to Warning."""

    raw = str(signal_id or "").strip().casefold().replace("-", "_").replace(" ", "_")
    resolved = ALIASES.get(raw, raw)
    return _by_id().get(resolved, _by_id()["warning"])


def resolve_runtime_signal(state: object, *, status: object = "") -> dict[str, str]:
    """Resolve existing runtime wording into the first-party OAP signal language."""

    raw_state = str(state or "").strip().casefold().replace("-", "_").replace(" ", "_")
    raw_status = str(status or "").strip().casefold()
    if raw_state in {"healthy", "ready", "live"}:
        return get_signal("healthy")
    if "not connected" in raw_status:
        return get_signal("offline")
    if "maintenance" in raw_status:
        return get_signal("maintenance")
    if "learning" in raw_status:
        return get_signal("learning")
    if raw_state:
        return get_signal(raw_state)
    return get_signal("warning")


def validate_signal_language() -> dict[str, Any]:
    ids = tuple(item["id"] for item in LIVE_SIGNALS)
    emojis = {item["id"]: item["emoji"] for item in LIVE_SIGNALS}
    errors: list[str] = []
    if len(ids) != len(set(ids)):
        errors.append("Duplicate OAP live signal IDs")
    if emojis.get("learning") != "🟣":
        errors.append("Learning must remain purple")
    if emojis.get("warning") != "🟡":
        errors.append("Warning must remain yellow")
    if emojis.get("healthy") != "🟢":
        errors.append("Healthy must remain green")
    if emojis.get("critical") != "🔴":
        errors.append("Critical must remain red")
    if any(item["emoji"] == "🟣" and item["id"] != "learning" for item in LIVE_SIGNALS):
        errors.append("Purple is reserved for Learning")
    return {
        "passed": not errors,
        "errors": tuple(errors),
        "signal_count": len(LIVE_SIGNALS),
        "first_party_only": True,
        "owner": "ON ANY POSTCODE",
    }


def public_legend() -> dict[str, Any]:
    validation = validate_signal_language()
    return {
        "name": "OAP Live Signal Legend",
        "owner": "ON ANY POSTCODE",
        "first_party_only": True,
        "signals": LIVE_SIGNALS,
        "groups": SIGNAL_GROUPS,
        "mind_body_soul": MIND_BODY_SOUL_SIGNALS,
        "verdict_rules": {
            "healthy": "🟢",
            "warning": "🟡",
            "critical": "🔴",
            "learning": "🟣",
            "learning_is_verdict": False,
            "purple_reserved_for_learning": True,
        },
        "external_identity_allowed": False,
        "external_authority_allowed": False,
        "can_approve": False,
        "can_execute": False,
        "validation": validation,
    }
