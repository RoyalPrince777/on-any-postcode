"""Civilian humanitarian emergency connectivity for SMI Technology Intelligence.

This module is for life-saving civilian communication in disasters and armed conflict.
It does not support targeting, surveillance, weapons, military command, troop tracking,
offensive cyber operations, or autonomous transmission. It prepares bounded,
privacy-minimised communication envelopes and connectivity recommendations while
keeping Human Authority final.
"""

from __future__ import annotations

from typing import Any

from .connectivity_runtime import connectivity_runtime_status

HUMANITARIAN_PRIORITIES: tuple[dict[str, Any], ...] = (
    {"id": "life_safety", "name": "Life Safety / SOS", "priority": 0},
    {"id": "medical", "name": "Medical Assistance", "priority": 1},
    {"id": "public_warning", "name": "Public Warning", "priority": 2},
    {"id": "family_reunification", "name": "Family Reunification", "priority": 3},
    {"id": "shelter_essentials", "name": "Shelter / Water / Food", "priority": 4},
    {"id": "aid_coordination", "name": "Humanitarian Aid Coordination", "priority": 5},
    {"id": "accessibility", "name": "Accessibility Support", "priority": 6},
)

HUMANITARIAN_FEATURES: tuple[dict[str, str], ...] = (
    {"id": "sos_queue", "name": "Offline-first SOS Queue", "purpose": "Prepare life-safety messages for store-and-forward delivery when links recover."},
    {"id": "multi_access", "name": "Multi-access Emergency Path Planner", "purpose": "Prefer available local/mobile paths and require mesh, roaming or satellite fallback."},
    {"id": "medical_priority", "name": "Medical Priority", "purpose": "Keep urgent medical communication ahead of non-life-safety traffic."},
    {"id": "family_reunification", "name": "Family Reunification", "purpose": "Prepare privacy-minimised reconnect messages for separated families."},
    {"id": "multilingual_alerts", "name": "Multilingual Public Alerts", "purpose": "Prepare alert content for later governed language and accessibility handling."},
    {"id": "data_minimisation", "name": "Humanitarian Data Minimisation", "purpose": "Avoid unnecessary identity, precise location and sensitive personal data."},
    {"id": "civilian_distinction", "name": "Civilian / Military Distinction Guard", "purpose": "Reject military, targeting, surveillance and weapon-support purposes."},
    {"id": "misinformation_guard", "name": "Public Warning Evidence Guard", "purpose": "Require source verification before broad public-warning dissemination."},
)

BLOCKED_MILITARY_PURPOSE_PHRASES = (
    "target coordinates",
    "target location",
    "select target",
    "strike target",
    "strike planning",
    "weapon guidance",
    "fire control",
    "track troops",
    "track combatants",
    "military surveillance",
    "military intelligence",
    "offensive cyber",
    "kill chain",
    "battlefield targeting",
)


def _priority(purpose: str) -> dict[str, Any] | None:
    normalized = purpose.strip().casefold()
    return next((item for item in HUMANITARIAN_PRIORITIES if item["id"] == normalized), None)


def _contains_prohibited_purpose(value: str) -> bool:
    normalized = " ".join(
        value.casefold().replace("/", " ").replace("_", " ").replace("-", " ").split()
    )
    return any(phrase in normalized for phrase in BLOCKED_MILITARY_PURPOSE_PHRASES)


def prepare_humanitarian_message(
    *,
    purpose: str,
    text: str,
    approximate_area: str | None = None,
    source_verified: bool = False,
    personal_data_required: bool = False,
) -> dict[str, Any]:
    """Prepare, but never transmit, one civilian humanitarian communication envelope."""

    priority = _priority(purpose)
    if priority is None:
        return {
            "accepted": False,
            "reason": "unsupported_humanitarian_purpose",
            "transmitted": False,
            "network_execution_authority": False,
            "human_authority_final": True,
        }
    if _contains_prohibited_purpose(text) or _contains_prohibited_purpose(purpose):
        return {
            "accepted": False,
            "reason": "civilian_distinction_guard",
            "transmitted": False,
            "network_execution_authority": False,
            "human_authority_final": True,
        }
    clean_text = " ".join(text.split()).strip()
    if not clean_text:
        return {
            "accepted": False,
            "reason": "empty_message",
            "transmitted": False,
            "network_execution_authority": False,
            "human_authority_final": True,
        }
    public_warning_blocked = purpose.strip().casefold() == "public_warning" and not source_verified
    return {
        "accepted": not public_warning_blocked,
        "reason": "source_verification_required" if public_warning_blocked else "prepared",
        "purpose": priority["id"],
        "priority": priority["priority"],
        "text": clean_text,
        "approximate_area": approximate_area.strip() if approximate_area else None,
        "precise_location_stored": False,
        "personal_data_required": bool(personal_data_required),
        "data_minimisation_required": True,
        "store_and_forward": True,
        "requires_human_review": True,
        "transmitted": False,
        "autonomous_transmission": False,
        "network_execution_authority": False,
        "human_authority_final": True,
    }


def humanitarian_path_plan() -> dict[str, Any]:
    """Return a civilian emergency connectivity plan from current production evidence."""

    runtime = connectivity_runtime_status()
    current_path = bool(runtime["production_software_ready"])
    return {
        "current_production_path_observed": current_path,
        "preferred_order": (
            "current_local_or_mobile_path",
            "emergency_mobile_roaming",
            "mesh_or_device_to_device",
            "community_wifi_or_local_relay",
            "satellite_fallback",
            "offline_store_and_forward",
        ),
        "second_independent_path_required": True,
        "offline_store_and_forward_required": True,
        "autonomous_network_switching": False,
        "human_authority_final": True,
    }


def humanitarian_connectivity_status() -> dict[str, Any]:
    """Return live production readiness for the civilian humanitarian emergency layer."""

    runtime = connectivity_runtime_status()
    production_path = bool(runtime["production_software_ready"])
    feature_matrix = tuple(
        {
            **feature,
            "architecture_ready": True,
            "production_software_ready": production_path,
            "can_execute": False,
        }
        for feature in HUMANITARIAN_FEATURES
    )
    return {
        "id": "international_humanitarian_connectivity",
        "name": "International Humanitarian Connectivity Intelligence",
        "mode": "civilian_emergency_production",
        "demo_mode": False,
        "production_software_ready": production_path,
        "international_reach_claim": False,
        "international_interoperability_target": True,
        "features": feature_matrix,
        "feature_count": len(feature_matrix),
        "priorities": HUMANITARIAN_PRIORITIES,
        "path_plan": humanitarian_path_plan(),
        "civilian_only": True,
        "military_command": False,
        "targeting": False,
        "surveillance": False,
        "weapon_support": False,
        "offensive_cyber": False,
        "precise_location_default": False,
        "autonomous_transmission": False,
        "network_execution_authority": False,
        "human_authority_final": True,
        "truth_boundary": (
            "Live production humanitarian communications software; no claim of global carrier "
            "reach, live 6G radio, or autonomous emergency dispatch."
        ),
    }
