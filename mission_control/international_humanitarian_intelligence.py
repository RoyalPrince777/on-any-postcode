"""Canonical civilian International Humanitarian Intelligence umbrella for SMI.

International Humanitarian Intelligence is the parent capability for civilian emergency
communications, maps, health information, essential aid, family reunification, public
warnings, accessibility, civilian safety and humanitarian legal/protection review. It does
not create a new SMI brain or Intelligence world and has no military, targeting,
surveillance, legal-adjudication or autonomous execution authority. Human Authority remains
final for OAP decisions.
"""

from __future__ import annotations

from typing import Any

from .humanitarian_connectivity import humanitarian_connectivity_status
from .humanitarian_legal_intelligence import humanitarian_legal_intelligence_status
from .humanitarian_map_intelligence import humanitarian_map_intelligence_status

INTERNATIONAL_HUMANITARIAN_SECTIONS: tuple[dict[str, str], ...] = (
    {
        "id": "connectivity",
        "name": "Humanitarian Connectivity Intelligence",
        "purpose": "Civilian SOS, medical-priority communications, resilient fallback and offline store-and-forward.",
    },
    {
        "id": "maps",
        "name": "Humanitarian Map Intelligence",
        "purpose": "Privacy-preserving civilian map context for places, hazards, access, connectivity and route readiness.",
    },
    {
        "id": "health",
        "name": "Humanitarian Health Intelligence",
        "purpose": "Evidence-bounded health information, urgent-care escalation and civilian care navigation without diagnosis authority.",
    },
    {
        "id": "aid_essentials",
        "name": "Humanitarian Aid & Essentials Intelligence",
        "purpose": "Prioritise verified civilian shelter, water, food, medical and essential-aid needs.",
    },
    {
        "id": "family_reunification",
        "name": "Family Reunification Intelligence",
        "purpose": "Support privacy-minimised reconnect workflows for separated civilians and families.",
    },
    {
        "id": "public_warning",
        "name": "Public Warning Intelligence",
        "purpose": "Prepare evidence-gated civilian alerts and reject unverified broad emergency warnings.",
    },
    {
        "id": "accessibility",
        "name": "Humanitarian Accessibility Intelligence",
        "purpose": "Make emergency information and movement context usable across disability, language and access needs.",
    },
    {
        "id": "civilian_safety",
        "name": "Civilian Safety Intelligence",
        "purpose": "Enforce civilian-only boundaries, data minimisation and no targeting, surveillance, weapons or military command.",
    },
    {
        "id": "legal",
        "name": "Humanitarian Legal Intelligence",
        "purpose": "Resolve potentially applicable IHL, human-rights, refugee, disaster, domestic, customary and specialist protection frameworks without issuing final legal advice.",
    },
)


def international_humanitarian_intelligence_status() -> dict[str, Any]:
    """Return the canonical International Humanitarian Intelligence hierarchy."""

    connectivity = humanitarian_connectivity_status()
    maps = humanitarian_map_intelligence_status()
    legal = humanitarian_legal_intelligence_status()
    section_ids = tuple(item["id"] for item in INTERNATIONAL_HUMANITARIAN_SECTIONS)
    architecture_ready = (
        len(section_ids) == len(set(section_ids))
        and len(section_ids) == 9
        and connectivity["mode"] == "civilian_emergency_production"
        and connectivity["demo_mode"] is False
        and connectivity["civilian_only"] is True
        and maps["mode"] == "civilian_emergency_map_production"
        and maps["demo_mode"] is False
        and maps["civilian_only"] is True
        and legal["architecture_ready"] is True
        and legal["civilian_only"] is True
        and legal["legal_advice_claim"] is False
    )
    return {
        "id": "international_humanitarian",
        "name": "International Humanitarian Intelligence",
        "kind": "cross_system_civilian_specialist_intelligence",
        "mode": "civilian_humanitarian_production",
        "demo_mode": False,
        "architecture_ready": architecture_ready,
        "brain_count": 0,
        "intelligence_world_count_added": 0,
        "section_count": len(INTERNATIONAL_HUMANITARIAN_SECTIONS),
        "sections": INTERNATIONAL_HUMANITARIAN_SECTIONS,
        "connectivity": connectivity,
        "maps": maps,
        "health": {
            "architecture_ready": True,
            "diagnosis_authority": False,
            "care_navigation": True,
            "urgent_escalation": True,
            "live_clinical_service_claim": False,
        },
        "aid_essentials": {
            "architecture_ready": True,
            "verified_source_required": True,
            "autonomous_dispatch": False,
            "live_global_supply_feed_claim": False,
        },
        "family_reunification": {
            "architecture_ready": True,
            "privacy_minimised": True,
            "precise_location_public": False,
            "autonomous_contacting": False,
        },
        "public_warning": {
            "architecture_ready": True,
            "source_verification_required": True,
            "autonomous_broadcast": False,
        },
        "accessibility": {
            "architecture_ready": True,
            "multilingual_target": True,
            "accessible_movement_context": True,
            "live_translation_claim": False,
        },
        "civilian_safety": {
            "architecture_ready": True,
            "civilian_only": True,
            "military_command": False,
            "targeting": False,
            "surveillance": False,
            "weapon_support": False,
            "offensive_cyber": False,
        },
        "legal": legal,
        "production_software_ready": bool(connectivity["production_software_ready"]),
        "production_navigation_ready": bool(maps["production_navigation_ready"]),
        "international_reach_claim": False,
        "live_humanitarian_data_feeds_claim": False,
        "live_jurisdiction_legal_feed_claim": False,
        "legal_advice_claim": False,
        "autonomous_dispatch": False,
        "autonomous_transmission": False,
        "network_execution_authority": False,
        "independent_execute": False,
        "independent_approval": False,
        "human_authority_final": True,
        "truth_boundary": (
            "International Humanitarian Intelligence is the live production software umbrella. "
            "Its child capabilities remain evidence-gated for physical navigation, worldwide "
            "carrier/satellite reach, live clinical services, live global humanitarian feeds and "
            "jurisdiction-specific legal conclusions."
        ),
    }
