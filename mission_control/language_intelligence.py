"""Governed Language Intelligence capability for SMI and OAP Education.

This capability reuses the validated OAP World language hub.  It does not create
a second language catalogue, persist learner speech, or claim live translation
coverage that is not connected.
"""

from __future__ import annotations

from typing import Any

from . import languages

LANGUAGE_INTELLIGENCE_COMPONENTS: tuple[dict[str, str], ...] = (
    {"id": "spoken", "name": "Spoken Language", "purpose": "Everyday speech, listening and conversation learning."},
    {"id": "literacy", "name": "Reading & Writing", "purpose": "Scripts, literacy, spelling and written communication."},
    {"id": "pronunciation", "name": "Pronunciation", "purpose": "Pronunciation and sound guidance with accuracy boundaries."},
    {"id": "translation", "name": "Translation Assistance", "purpose": "Governed translation support without pretending automated output is authoritative."},
    {"id": "culture", "name": "Cultural Context", "purpose": "Meaning, etiquette, register and local language context."},
    {"id": "work", "name": "Work & Trade Language", "purpose": "Practical language for jobs, trades, services and business."},
    {"id": "esol", "name": "ESOL & Language Learning", "purpose": "English and other-language learning pathways from beginner upward."},
    {"id": "sign", "name": "Sign Language", "purpose": "Sign-language discovery and learning paths with regional variation preserved."},
    {"id": "accessibility", "name": "Accessible Language", "purpose": "Plain-language and accessibility-aware communication support."},
    {"id": "heritage", "name": "Heritage Languages", "purpose": "Heritage, endangered and community language knowledge with provenance."},
    {"id": "earth", "name": "Earth Language Context", "purpose": "Connect languages to real countries, regions, communities and variants."},
    {"id": "youth", "name": "Youth Language Learning", "purpose": "Age-appropriate language learning inside Youth Club safeguards."},
)


def validate_language_intelligence() -> dict[str, Any]:
    ids = [item["id"] for item in LANGUAGE_INTELLIGENCE_COMPONENTS]
    errors: list[str] = []
    if len(ids) != len(set(ids)):
        errors.append("Duplicate Language Intelligence component IDs")
    hub = languages.validate_language_hub()
    if not hub["passed"]:
        errors.extend(f"Language hub: {error}" for error in hub["errors"])
    if languages.PUBLIC_BOUNDARY.get("stores_progress"):
        errors.append("Public Language Intelligence must not silently store progress")
    if languages.PUBLIC_BOUNDARY.get("records_audio"):
        errors.append("Public Language Intelligence must not silently record audio")
    return {
        "passed": not errors,
        "errors": errors,
        "component_count": len(ids),
        "language_hub": hub,
    }


def language_intelligence_status() -> dict[str, Any]:
    validation = validate_language_intelligence()
    return {
        "name": "Language Intelligence",
        "kind": "cross_system_capability",
        "architecture_passed": validation["passed"],
        "component_count": len(LANGUAGE_INTELLIGENCE_COMPONENTS),
        "components": tuple(dict(item) for item in LANGUAGE_INTELLIGENCE_COMPONENTS),
        "oap_world_language_hub_connected": validation["language_hub"]["passed"],
        "earth_intelligence_connection": "place_language_context",
        "life_intelligence_connection": "education_and_practical_use",
        "link_up_connection": "future_governed_multilingual_tools",
        "live_translation_ready": False,
        "speech_learning_ready": False,
        "learner_progress_ready": False,
        "youth_safeguarding_required": True,
        "human_authority_final": True,
        "can_execute": False,
        "truth_boundary": (
            "The validated read-only language hub is live. Full translation, speech, "
            "progress and protected multilingual communication remain separately gated."
        ),
    }
