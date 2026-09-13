"""Evidence-aware runtime proof matrix for all governed OAP Intelligence.

Bounded runtime, live evidence and complete production runtime are separate claims.
Architecture or owned-runtime proof never upgrades missing external-world evidence
automatically.
"""
from __future__ import annotations

import os
from typing import Any

from oap.guardian import GuardianEngine

from . import (
    all_intelligence,
    earth_intelligence,
    ecosystem_intelligence,
    international_humanitarian_intelligence,
    language_intelligence,
    life_intelligence,
    location_intelligence,
    media_intelligence,
    movement_intelligence,
    movement_proof,
    smi_receipt_backend,
    technology_intelligence,
    telemetry,
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


def _render_runtime_present() -> bool:
    commit = os.getenv("RENDER_GIT_COMMIT", "").strip()
    identity = (
        os.getenv("RENDER_SERVICE_ID", "").strip()
        or os.getenv("RENDER_EXTERNAL_URL", "").strip()
        or os.getenv("RENDER_SERVICE_NAME", "").strip()
    )
    return bool(commit and identity)


def status() -> dict[str, Any]:
    """Return a read-only proof matrix without making network calls."""

    location_status = location_intelligence.status()
    weather_verified = bool(location_status["weather_provider_verified"])
    earth = earth_intelligence.status(weather_ready=weather_verified)
    language = language_intelligence.language_intelligence_status()
    life = life_intelligence.life_intelligence_status()
    movement = movement_intelligence.movement_intelligence_status()
    movement_runtime = movement_proof.status()
    technology = technology_intelligence.technology_intelligence_status()
    humanitarian = (
        international_humanitarian_intelligence.international_humanitarian_intelligence_status()
    )
    ecosystem = ecosystem_intelligence.status()
    receipt_config = smi_receipt_backend.backend_configuration_status()
    hierarchy = all_intelligence.status()
    hierarchy_worlds = {str(item["id"]): item for item in hierarchy["worlds"]}
    local_telemetry = telemetry.status()
    guardian = GuardianEngine().status()

    local_observability = bool(local_telemetry.get("local_observability_ready"))
    infrastructure_live = bool(local_observability and _render_runtime_present())
    people_aggregate_live = bool(
        int(local_telemetry.get("local_request_count") or 0) > 0
        and local_telemetry.get("local_last_request_epoch") is not None
    )
    trust_live = bool(guardian.get("ready") and local_observability)

    multimodal_preparation_ready = bool(
        media_intelligence.DOCUMENT_MIMES
        and media_intelligence.AUDIO_MIMES
        and media_intelligence.IMAGE_MIMES
        and media_intelligence.MAX_VIDEO_FRAMES > 0
    )

    civic_architecture = bool(
        hierarchy_worlds.get("civic", {}).get("architecture_ready")
        and hierarchy_worlds.get("civic", {}).get("routing_ready")
    )
    civilisation_architecture = bool(
        hierarchy_worlds.get("civilisation", {}).get("architecture_ready")
        and hierarchy_worlds.get("civilisation", {}).get("routing_ready")
    )

    worlds = (
        _proof(
            item_id="earth",
            name="Earth Intelligence",
            bounded_runtime_ready=bool(
                earth["nature_organ_connected"] and earth["the_spot_connected"]
            ),
            live_external_ready=weather_verified,
            full_runtime_ready=bool(earth["full_earth_runtime_ready"]),
            bounded_evidence="OAP Nature, The Spot and Local-to-Global place model are connected.",
            next_gate=(
                "Weather observation source is proven in-process; prove wider water, ecosystem, agriculture, resource and disaster sources."
                if weather_verified
                else "Trigger a real bounded Weather refresh, then prove wider water, ecosystem, agriculture, resource and disaster sources."
            ),
        ),
        _proof(
            item_id="language",
            name="Language Intelligence",
            bounded_runtime_ready=bool(language["oap_world_language_hub_connected"]),
            live_external_ready=bool(
                language["live_translation_ready"] or language["speech_learning_ready"]
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
            bounded_runtime_ready=bool(life["architecture_passed"]),
            live_external_ready=bool(
                life["credential_runtime_ready"]
                or life["apprenticeship_runtime_ready"]
                or life["market_opportunity_runtime_ready"]
            ),
            full_runtime_ready=bool(
                life["credential_runtime_ready"]
                and life["apprenticeship_runtime_ready"]
                and life["market_opportunity_runtime_ready"]
            ),
            bounded_evidence="Validated Adult/Youth practical-life, trade, profession and safety architecture executes as a governed read-only capability.",
            next_gate="Connect certified credential, apprenticeship and Market opportunity evidence without treating OAP learning as a regulated licence.",
        ),
        _proof(
            item_id="movement",
            name="Movement Intelligence",
            bounded_runtime_ready=bool(
                movement_runtime["route_proof_ready"] and movement_runtime["request_preview_ready"]
            ),
            live_external_ready=False,
            full_runtime_ready=bool(movement["production_navigation_ready"]),
            bounded_evidence="Public first-party seed route proof and request preview execute without dispatch, payment or hidden tracking.",
            next_gate=str(movement_runtime["next_gate"]),
        ),
        _proof(
            item_id="civic",
            name="Civic Intelligence",
            bounded_runtime_ready=civic_architecture,
            live_external_ready=False,
            full_runtime_ready=False,
            bounded_evidence="Canonical Civic Intelligence world, families and governed routing are executable and registry-aligned; current civic/public-service source proof remains separate.",
            next_gate="Add source-scoped local-service, civic-state and public-information proof adapters.",
        ),
        _proof(
            item_id="civilisation",
            name="Civilisation Intelligence",
            bounded_runtime_ready=civilisation_architecture,
            live_external_ready=False,
            full_runtime_ready=False,
            bounded_evidence="Canonical Civilisation Intelligence routing and registered specialist families, including Nirmata placement, are executable and registry-aligned.",
            next_gate="Connect provenance-backed history, culture, heritage and institution sources without replacing HRM memory.",
        ),
        _proof(
            item_id="matrix",
            name="Matrix Intelligence",
            bounded_runtime_ready=bool(technology["production_software_ready"]),
            live_external_ready=infrastructure_live,
            full_runtime_ready=False,
            bounded_evidence="Governed production software, spatial/technology intelligence and Matrix agent placement are implemented.",
            next_gate=(
                "Fresh hosted runtime telemetry is proven; continue with physical testbeds, network evidence and hardware attestations capability by capability."
                if infrastructure_live
                else "Prove fresh hosted runtime telemetry, then physical testbeds and hardware/network evidence capability by capability."
            ),
        ),
    )

    ecosystem_bounded = bool(
        len(ecosystem["domains"]) == 10
        and len(ecosystem["pressure_dimensions"]) == 9
        and ecosystem["matrix_signal_bus"] == "required"
        and ecosystem["human_authority"] == "final"
    )
    ecosystem_live_any = bool(
        weather_verified or infrastructure_live or people_aggregate_live or trust_live
    )

    cross_system = (
        _proof(
            item_id="ecosystem",
            name="Ecosystem Intelligence",
            bounded_runtime_ready=ecosystem_bounded,
            live_external_ready=ecosystem_live_any,
            full_runtime_ready=False,
            bounded_evidence=(
                "Ten-domain contextual reasoning, NOW/NEXT/TREND, truth-state separation, "
                "cross-postcode learning, Matrix routing and Founder decision packs are implemented."
            ),
            next_gate=(
                "Prove every remaining external source lane and independent durable HRM write/read. "
                + (
                    "Independent HRM Postgres is configured but still requires runtime write/read proof."
                    if receipt_config["durable_backend_configured"]
                    else "Configure OAP_HRM_DATABASE_URL for the independent Render Postgres receipt store."
                )
            ),
        ),
        _proof(
            item_id="technology",
            name="Technology Intelligence",
            bounded_runtime_ready=bool(technology["production_software_ready"]),
            live_external_ready=bool(
                technology["6g_production_network_ready"]
                or technology["isac_physical_testbed_ready"]
                or infrastructure_live
            ),
            full_runtime_ready=bool(
                technology["6g_production_network_ready"]
                and technology["isac_physical_testbed_ready"]
                and technology["spatial_capture_hardware_proven"]
                and technology["spatial_display_hardware_proven"]
            ),
            bounded_evidence="Production-mode advisory software and owned hosted-runtime telemetry are separated from unproven telecom/operator authority.",
            next_gate="Supply signed physical radio, spatial hardware and live network evidence before hardware/network full-green claims.",
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
            bounded_evidence="Civilian-only tracker, SMI context and authoritative-source adapters are implemented with fail-closed source handling.",
            next_gate="Run a live source-health pass and separately prove physical navigation, clinical, carrier/satellite and jurisdiction feeds.",
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
        "weather_provider_verified": weather_verified,
        "infrastructure_runtime_verified": infrastructure_live,
        "people_aggregate_verified": people_aggregate_live,
        "guardian_runtime_verified": trust_live,
        "network_calls_made": False,
        "universal_runtime_green": full_count == len(worlds),
        "universal_runtime_light": _light(full_count == len(worlds)),
        "execution_granted": False,
        "approval_granted": False,
        "human_authority_final": True,
        "truth_boundary": (
            "Bounded runtime, live evidence and full runtime are separate claims. "
            "Owned telemetry or a green source proof never implies universal live-world readiness."
        ),
    }
