"""Governed real-time capability model for OAP Link Up.

This module defines the product contract for Voice, Call, Face Up, sharing,
presence and OAP Motion. It deliberately does not claim transport or motion
assets are live: each capability stays fail-closed until its explicit runtime
gates pass.
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

REALTIME_CAPABILITIES: tuple[dict[str, object], ...] = (
    {
        "id": "voice",
        "name": "Voice",
        "kind": "voice_note",
        "requires": ("microphone_permission", "media_store", "guardian_scan"),
        "status": "locked",
    },
    {
        "id": "call",
        "name": "Call",
        "kind": "audio_call",
        "requires": ("microphone_permission", "signalling", "turn_fallback", "call_audit_metadata"),
        "status": "locked",
    },
    {
        "id": "face_up",
        "name": "Face Up",
        "kind": "video_call",
        "requires": (
            "microphone_permission",
            "camera_permission",
            "signalling",
            "turn_fallback",
            "call_audit_metadata",
        ),
        "status": "locked",
    },
    {
        "id": "media",
        "name": "Share",
        "kind": "media_share",
        "requires": ("media_store", "content_type_validation", "guardian_scan"),
        "status": "locked",
    },
    {
        "id": "files",
        "name": "Files",
        "kind": "file_share",
        "requires": ("private_file_store", "size_limits", "content_type_validation", "guardian_scan"),
        "status": "locked",
    },
    {
        "id": "around_now",
        "name": "Around Now",
        "kind": "presence",
        "requires": ("presence_store", "expiry", "per_link_visibility"),
        "status": "locked",
    },
    {
        "id": "live_spot",
        "name": "Live Spot",
        "kind": "live_location",
        "requires": (
            "location_permission",
            "presence_store",
            "expiry",
            "per_link_visibility",
            "explicit_live_spot_stop",
        ),
        "status": "locked",
    },
)

PRIVACY_DIAL_DEFAULTS: dict[str, bool] = {
    "voice": True,
    "call": False,
    "face_up": False,
    "media": True,
    "files": True,
    "around_now": False,
    "share_my_spot": False,
    "live_spot": False,
}

RUNTIME_GATES: dict[str, bool] = {
    "authenticated_identity": True,
    "accepted_link_required": True,
    "block_guard": True,
    "explicit_device_permission": True,
    "phone_number_required": False,
    "public_media_projection": False,
    "record_calls_by_default": False,
    "human_authority_final": True,
}

OAP_MOTION_SYSTEM: dict[str, object] = {
    "name": "OAP Motion",
    "ownership": "first_party",
    "renderer": "local_svg_css",
    "external_emoji_provider_required": False,
    "motion_must_mean_something": True,
    "reduced_motion_required": True,
    "static_fallback_required": True,
    "offline_safe_required": True,
}

OAP_MOTION_SIGNALS: tuple[dict[str, str], ...] = (
    {"id": "im_free", "name": "I'm Free", "fallback": "🟢", "motion": "soft pulse"},
    {"id": "link_up", "name": "Link Up", "fallback": "🔗", "motion": "join and lock"},
    {"id": "seen", "name": "Seen", "fallback": "👀", "motion": "open once then settle"},
    {"id": "live_spot", "name": "Live Spot", "fallback": "📍", "motion": "bounded outward pulse"},
    {"id": "voice", "name": "Voice", "fallback": "🎙️", "motion": "waveform"},
    {"id": "call", "name": "Call", "fallback": "📞", "motion": "ring"},
    {"id": "face_up", "name": "Face Up", "fallback": "📹", "motion": "frame open"},
    {"id": "bring_in", "name": "Bring In", "fallback": "🤝", "motion": "join"},
    {"id": "around_now", "name": "Around Now", "fallback": "🌍", "motion": "slow orbit"},
    {"id": "pulse", "name": "Pulse", "fallback": "⚡", "motion": "heartbeat"},
    {"id": "learning", "name": "Learning", "fallback": "🟣", "motion": "soft glow"},
    {"id": "thinking", "name": "Thinking", "fallback": "🟡", "motion": "bounded orbit"},
    {"id": "urgent", "name": "Urgent", "fallback": "🔴", "motion": "controlled double pulse"},
    {"id": "human_authority", "name": "Human Authority", "fallback": "👑", "motion": "restrained shimmer"},
    {"id": "mind_working", "name": "Mind Working", "fallback": "🧠", "motion": "node flow"},
)

OAP_MOTION_RUNTIME_REQUIREMENTS: tuple[str, ...] = (
    "first_party_motion_assets",
    "reduced_motion_static_fallback",
    "accessible_labels",
    "offline_asset_availability",
)


def capability_state(runtime: Mapping[str, bool] | None = None) -> list[dict[str, Any]]:
    """Return fail-closed capability state from explicit runtime evidence."""
    evidence = dict(runtime or {})
    result: list[dict[str, Any]] = []
    for capability in REALTIME_CAPABILITIES:
        required = tuple(str(item) for item in capability["requires"])
        missing = [gate for gate in required if evidence.get(gate) is not True]
        result.append(
            {
                "id": capability["id"],
                "name": capability["name"],
                "kind": capability["kind"],
                "ready": not missing,
                "missing": missing,
            }
        )
    return result


def privacy_dial(overrides: Mapping[str, object] | None = None) -> dict[str, bool]:
    """Return a strict per-Link permission set, ignoring unknown permissions."""
    values = dict(PRIVACY_DIAL_DEFAULTS)
    for key, value in dict(overrides or {}).items():
        if key in values and isinstance(value, bool):
            values[key] = value
    return values


def motion_state(runtime: Mapping[str, bool] | None = None) -> dict[str, Any]:
    """Keep OAP Motion fail-closed until local, accessible assets are evidenced."""
    evidence = dict(runtime or {})
    missing = [
        requirement
        for requirement in OAP_MOTION_RUNTIME_REQUIREMENTS
        if evidence.get(requirement) is not True
    ]
    return {
        "name": OAP_MOTION_SYSTEM["name"],
        "ready": not missing,
        "missing": missing,
        "signals": len(OAP_MOTION_SIGNALS),
    }
