"""Governed real-time capability model for OAP Link Up.

This module defines the product contract for voice notes, audio calls, Face Up
video, media/file sharing and presence. It deliberately does not claim transport
is live: each capability stays fail-closed until its explicit runtime gates pass.
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
        "name": "Media",
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
)

PRIVACY_DIAL_DEFAULTS: dict[str, bool] = {
    "voice": True,
    "call": False,
    "face_up": False,
    "media": True,
    "files": True,
    "around_now": False,
    "share_my_spot": False,
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
