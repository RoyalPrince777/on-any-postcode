"""Evidence-aware runtime proof matrix for all governed OAP Intelligence.

This module distinguishes three different claims that must never be collapsed:

1. bounded_runtime_ready: owned code/surface can execute its present bounded role;
2. live_external_ready: required current external/source/hardware proof is present;
3. full_runtime_ready: the complete intended capability is production-proven.

A green bounded-runtime light never upgrades the wider capability. Human Authority
remains final and this module grants no execution or approval authority.
"""

from __future__ import annotations

from typing import Any

from . import (
    earth_intelligence,
    international_humanitarian_intelligence,
    language_intelligence,
    life_intelligence,
    media_intelligence,
    movement_intelligence,
    movement_proof,
    technology_intelligence,
)

CANONICAL_WORLD_IDS: tuple[str, ...] = (
    "earth",
    "language",
    "life",
    "movement",
    "civic",
    "civilisation",
    "matrix",
)


def _light(value: bool) -> str:
    return "🟢" if value else "🟣"


def _proof(
    *,
    item_id: str,
    name: str,
    bounded_runtime_ready: bool,
    live_external_ready: bool,
    full_runtime_ready: bool,
    bounded_evidence: str,
    next_gate: str,
) -> dict[str, Any]:
    return {
        "id": item_id,
        "name": name,
        "bounded_runtime_ready": bool(bounded_runtime_ready),
        "bounded_runtime_light": _light(bool(bounded_runtime_ready)),
        "live_external_ready": bool(live_external_ready),
        "live_external_light": _light(bool(live_external_ready)),
        "full_runtime_ready": bool(full_runtime_ready),
        "full_runtime_light": _light(bool(full_runtime_ready)),
        "bounded_evidence": bounded_evidence,
        "next_gate": next_gate,
    }


def status() -> dict[str, Any]:
    """Return a read-only proof matrix without making network calls."""

    earth = earth_intelligence.status(weather_ready=False)
    language = language_intelligence.language_intelligence_status()
    life = life_intelligence.life_intelligence_status()
    movement = movement_intelligence.movement_intelligence_status()
    movement_runtime = movement_proof.status()
    technology = technology_intelligence.technology_intelligence_status()
    humanitarian = (
        international_humanitarian_intelligence.international_humanitarian_intelligence_status()
    )

    multimodal_preparation_ready = bool(
        media_intelligence.DOCUMENT_MIMES
        and media_intelligence.AUDIO_MIMES
        and media_intelligence.IMAGE_MIMES
        and media_intelligence.MAX_VIDEO_FRAMES > 0
    )

    worlds = (
        _proof(
            item_id="earth",
            name="Earth Intelligence",
            bounded_runtime_ready=bool(
                earth["nature_organ_connected"] and earth["the_spot_connected"]
            ),
            live_external_ready=bool(earth["weather_intelligence_connected"]),
            full_runtime_ready=bool(earth["full_earth_runtime_ready"]),
            bounded_evidence="OAP Nature, The Spot and Local-to-Global place model are connected.",
            next_gate="Prove live Weather plus wider water, ecosystem, agriculture, resource and disaster sources.",
        ),
        _proof(
            item_id="language",
            name="Language Intelligence",
            bounded_runtime_ready=bool(language["oap_world_language_hub_connected"]),
            live_external_ready=bool(
                language["live_translation_ready"]
                or language["speech_learning_ready"]
            ),
            full_runtime_ready=bool(
                language["live_translation_ready"]
                and language["speech_learning_ready"]
                and language["learner_progress_ready"]
            ),
            bounded_evidence="Validated read-only OAP World language hub is connected.",
            next_gate="Prove live translation, speech learning and protected learner progress separately.",
        ),
        _proof(
            item_id="life",
            name="Life Intelligence",
            bounded_runtime_ready=False,
            live_external_ready=False,
            full_runtime_ready=False,
            bounded_evidence="Practical-life, trade, profession and Youth/Adult architecture is validated; operational learning supply is not yet proven.",
            next_gate="Connect governed credential, apprenticeship and Market opportunity runtimes with certified evidence.",
        ),
        _proof(
            item_id="movement",
            name="Movement Intelligence",
            bounded_runtime_ready=bool(
                movement_runtime["route_proof_ready"]
                and movement_runtime["request_preview_ready"]
            ),
            live_external_ready=False,
            full_runtime_ready=bool(movement["production_navigation_ready"]),
            bounded_evidence="Public first-party seed route proof and request preview execute without dispatch, payment or hidden tracking.",
            next_gate=str(movement_runtime["next_gate"]),
        ),
        _proof(
            item_id="civic",
            name="Civic Intelligence",
            bounded_runtime_ready=False,
            live_external_ready=False,
            full_runtime_ready=False,
            bounded_evidence="Civic agent family and cross-world routing are registered; a dedicated current public-service runtime proof is not yet connected.",
            next_gate="Add source-scoped local-service, civic-state and public-information proof adapters.",
        ),
        _proof(
            item_id="civilisation",
            name="Civilisation Intelligence",
            bounded_runtime_ready=False,
            live_external_ready=False,
            full_runtime_ready=False,
            bounded_evidence="Civilisation, Akan Core and Akan Animal families are registered; live provenance-backed culture/history runtime evidence is not yet connected.",
            next_gate="Connect provenance-backed history, culture, heritage and institution sources without replacing HRM memory.",
        ),
        _proof(
            item_id="matrix",
            name="Matrix Intelligence",
            bounded_runtime_ready=bool(technology["production_software_ready"]),
            live_external_ready=False,
            full_runtime_ready=False,
            bounded_evidence="Governed production software, spatial/technology intelligence and Matrix agent placement are implemented.",
            next_gate="Prove physical testbeds, live infrastructure/source telemetry and hardware/network evidence capability by capability.",
        ),
    )

    cross_system = (
        _proof(
            item_id="technology",
            name="Technology Intelligence",
            bounded_runtime_ready=bool(technology["production_software_ready"]),
            live_external_ready=bool(
                technology["6g_production_network_ready"]
                or technology["isac_physical_testbed_ready"]
            ),
            full_runtime_ready=bool(
                technology["6g_production_network_ready"]
                and technology["isac_physical_testbed_ready"]
                and technology["spatial_capture_hardware_proven"]
                and technology["spatial_display_hardware_proven"]
            ),
            bounded_evidence="Production-mode advisory software is present; no telecom/operator authority is claimed.",
            next_gate="Supply signed physical radio, spatial hardware and live network evidence before hardware/network green claims.",
        ),
        _proof(
            item_id="international_humanitarian",
            name="International Humanitarian Intelligence",
            bounded_runtime_ready=bool(
                humanitarian["production_software_ready"]
                and humanitarian["multi_source_emergency_tracker_ready"]
                and humanitarian["humanitarian_tracker_smi_context_ready"]
            ),
            live_external_ready=False,
            full_runtime_ready=False,
            bounded_evidence="Civilian-only tracker, SMI context and source adapters are implemented with fail-closed source handling.",
            next_gate="Record live source-health evidence and separately prove physical navigation, clinical, carrier/satellite and jurisdiction feeds.",
        ),
        _proof(
            item_id="multimodal",
            name="Multimodal Intelligence",
            bounded_runtime_ready=multimodal_preparation_ready,
            live_external_ready=False,
            full_runtime_ready=False,
            bounded_evidence="SMI validates documents, images, audio and sampled-video preparation with raw attachment retention disabled.",
            next_gate="Add provider/source health attestation for document, image, transcription and sampled-video execution without treating provider availability as permanent.",
        ),
    )

    bounded_count = sum(bool(item["bounded_runtime_ready"]) for item in worlds)
    live_count = sum(bool(item["live_external_ready"]) for item in worlds)
    full_count = sum(bool(item["full_runtime_ready"]) for item in worlds)

    return {
        "component": "All Intelligence Runtime Proof",
        "world_count": len(worlds),
        "world_ids": tuple(str(item["id"]) for item in worlds),
        "worlds": worlds,
        "cross_system": cross_system,
        "bounded_runtime_proven": bounded_count,
        "bounded_runtime_total": len(worlds),
        "live_external_proven": live_count,
        "live_external_total": len(worlds),
        "full_runtime_proven": full_count,
        "full_runtime_total": len(worlds),
        "universal_runtime_green": full_count == len(worlds),
        "universal_runtime_light": _light(full_count == len(worlds)),
        "network_calls_made": False,
        "execution_granted": False,
        "approval_granted": False,
        "human_authority_final": True,
        "truth_boundary": (
            "Bounded runtime, live external proof and full runtime are separate claims. "
            "A green bounded runtime never implies full live-world readiness."
        ),
    }
