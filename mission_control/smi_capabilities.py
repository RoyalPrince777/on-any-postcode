"""Unified read-only capability registry for Sovereign Megaverse Intelligence.

This projection joins the locked seven Intelligence worlds with cross-system
capabilities without turning those capabilities into extra worlds, agent
families, brains or authority holders.
"""

from __future__ import annotations

from typing import Any

from oap.smi.agi_core import AGICore
from oap.smi.command_intelligence import CommandIntelligence
from oap.smi.sovereign_controls import SovereignControlPlane

from . import (
    earth_intelligence,
    language_intelligence,
    life_intelligence,
    movement_intelligence,
)
from .agents import INTELLIGENCE_WORLDS

CROSS_SYSTEM_CAPABILITIES: tuple[dict[str, str], ...] = (
    {
        "id": "language",
        "name": "Language Intelligence",
        "purpose": "Communication, language learning, translation assistance and cultural language context.",
    },
    {
        "id": "life",
        "name": "Life Intelligence",
        "purpose": "Real facts, real skills and practical Adult/Youth education through Community Power.",
    },
    {
        "id": "movement",
        "name": "Movement Intelligence",
        "purpose": "People, goods, services, routes, transport, logistics and movement conditions.",
    },
    {
        "id": "multimodal",
        "name": "Multimodal Intelligence",
        "purpose": "Governed image, document, audio and sampled-video understanding through existing SMI media preparation.",
    },
)

SMI_INTERNAL_CAPABILITIES: tuple[dict[str, str], ...] = (
    {
        "id": "agi_core",
        "name": "AGI Core",
        "kind": "capability_layer",
        "purpose": "Routes and synthesises across specialist intelligence without claiming achieved AGI.",
    },
    {
        "id": "command_intelligence",
        "name": "SMI Command Intelligence",
        "kind": "bounded_command_capability_chain",
        "purpose": "SGI → TGI → OGI → DGI → PGI → RGI advisory command review with no action authority.",
    },
    {
        "id": "sovereign_controls",
        "name": "SMI Sovereign Control Plane",
        "kind": "fail_closed_control_plane",
        "purpose": "Central technical ownership, approval, audit, egress, emergency-halt and execution boundaries.",
    },
    {
        "id": "synthetic_mind",
        "name": "Synthetic Mind Intelligence",
        "kind": "internal_organ",
        "purpose": "Synthetic reasoning and provider/advisor synthesis inside the single SMI brain.",
    },
    {
        "id": "biological_brain",
        "name": "Biological Brain Anatomy",
        "kind": "internal_regions",
        "purpose": "Real brain-inspired routing, memory, risk, planning, integration and coordination regions.",
    },
    {
        "id": "hrm",
        "name": "HRM Memory & Learning",
        "kind": "memory",
        "purpose": "Durable evidence, outcomes, lessons and audit-aware learning.",
    },
    {
        "id": "judgement",
        "name": "Judgement",
        "kind": "decision_review",
        "purpose": "Five automated evidence/review sections plus the Human Authority decision section.",
    },
    {
        "id": "war_room",
        "name": "War Room",
        "kind": "simulation",
        "purpose": "Consequence simulation and dissent without final decision authority.",
    },
    {
        "id": "guardian",
        "name": "Guardian & Aegis",
        "kind": "protection",
        "purpose": "Safety, privacy, constitutional and threat boundaries.",
    },
    {
        "id": "providers",
        "name": "Provider Fabric",
        "kind": "provider_layer",
        "purpose": "Approved local/cloud model providers remain providers, never OAP agents or authority.",
    },
    {
        "id": "agents",
        "name": "Agent Registry",
        "kind": "advisory_workers",
        "purpose": "Soul–Mind–Body advisory agents with one family each and bounded roles.",
    },
    {
        "id": "execution",
        "name": "Living Kernel / Builder Boundary",
        "kind": "human_gated_execution",
        "purpose": "Only recorded Human Authority approval can cross into consequential execution.",
    },
)


def validate_smi_capabilities() -> dict[str, Any]:
    world_ids = [str(item["id"]) for item in INTELLIGENCE_WORLDS]
    cross_ids = [item["id"] for item in CROSS_SYSTEM_CAPABILITIES]
    internal_ids = [item["id"] for item in SMI_INTERNAL_CAPABILITIES]
    errors: list[str] = []
    if len(world_ids) != 7 or len(world_ids) != len(set(world_ids)):
        errors.append("The seven Intelligence worlds must remain exactly seven and unique")
    if len(cross_ids) != len(set(cross_ids)):
        errors.append("Cross-system Intelligence capability IDs must be unique")
    if len(internal_ids) != len(set(internal_ids)):
        errors.append("Internal SMI capability IDs must be unique")
    if set(cross_ids) & set(world_ids):
        errors.append("Cross-system capabilities must not silently become Intelligence worlds")

    agi = AGICore().status()
    if agi["brain_count"] != 0 or agi["independent_execute"] or agi["independent_approval"]:
        errors.append("AGI Core escaped its bounded capability-layer role")
    if agi["agi_achieved"] or agi["general_intelligence_certified"]:
        errors.append("Architecture must not claim achieved/certified AGI without proof")

    command = CommandIntelligence().status()
    expected_command_path = ("sgi", "tgi", "ogi", "dgi", "pgi", "rgi")
    if command["brain_count"] != 0:
        errors.append("Command Intelligence must not create another SMI brain")
    if command["command_path"] != expected_command_path:
        errors.append("SMI command path must remain SGI → TGI → OGI → DGI → PGI → RGI")
    if command["independent_execute"] or command["independent_approval"]:
        errors.append("Command Intelligence must remain advisory and human-gated")
    if command["prediction_claims_fact"]:
        errors.append("PGI forecasts must never be represented as facts")
    if not command["fail_closed_resilience"]:
        errors.append("RGI must preserve fail-closed resilience")

    sovereign = SovereignControlPlane().status()
    if sovereign["brain_count"] != 0:
        errors.append("Sovereign controls must not create another SMI brain")
    if sovereign["independent_execute"] or sovereign["independent_approval"]:
        errors.append("Sovereign controls must not become an authority holder")
    if sovereign["external_provider_egress_default"] != "deny":
        errors.append("External provider egress must default to deny")
    if sovereign["secret_export"]:
        errors.append("Sovereign controls must never enable secret export")
    if not sovereign["human_authority_final"]:
        errors.append("Human Authority must remain final")

    specialist = {
        "earth": earth_intelligence.status(weather_ready=False),
        "language": language_intelligence.language_intelligence_status(),
        "life": life_intelligence.life_intelligence_status(),
        "movement": movement_intelligence.movement_intelligence_status(),
    }
    if not all(bool(item.get("architecture_passed")) for item in specialist.values()):
        errors.append("One or more specialist Intelligence architecture checks failed")
    return {
        "passed": not errors,
        "errors": errors,
        "checks": {
            "intelligence_worlds": len(world_ids),
            "cross_system_capabilities": len(cross_ids),
            "internal_capabilities": len(internal_ids),
            "brain_count_added_by_agi": agi["brain_count"],
            "brain_count_added_by_command_intelligence": command["brain_count"],
            "brain_count_added_by_sovereign_controls": sovereign["brain_count"],
            "command_stages": command["stage_count"],
            "external_provider_egress_default": sovereign[
                "external_provider_egress_default"
            ],
            "human_authority_final": True,
        },
    }


def smi_capability_status() -> dict[str, Any]:
    validation = validate_smi_capabilities()
    return {
        "name": "Sovereign Megaverse Intelligence",
        "architecture_passed": validation["passed"],
        "validation": validation,
        "agi_core": AGICore().status(),
        "command_intelligence": CommandIntelligence().status(),
        "sovereign_controls": SovereignControlPlane().status(),
        "intelligence_worlds": tuple(dict(item) for item in INTELLIGENCE_WORLDS),
        "cross_system_capabilities": CROSS_SYSTEM_CAPABILITIES,
        "internal_capabilities": SMI_INTERNAL_CAPABILITIES,
        "specialist_status": {
            "earth": earth_intelligence.status(weather_ready=False),
            "language": language_intelligence.language_intelligence_status(),
            "life": life_intelligence.life_intelligence_status(),
            "movement": movement_intelligence.movement_intelligence_status(),
        },
        "human_authority_final": True,
        "independent_execution": False,
    }
