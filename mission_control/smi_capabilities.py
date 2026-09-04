"""Unified read-only capability registry for Sovereign Megaverse Intelligence.

This projection joins the locked seven Intelligence Worlds with cross-system
capabilities without turning those capabilities into extra worlds, agent
families, brains or authority holders.
"""

from __future__ import annotations

from typing import Any

from oap.smi import intelligence_capability_registry
from oap.smi.agi_core import AGICore
from oap.smi.command_intelligence import CommandIntelligence
from oap.smi.sovereign_controls import SovereignControlPlane

from . import (
    earth_intelligence,
    international_humanitarian_intelligence,
    language_intelligence,
    life_intelligence,
    movement_intelligence,
    technology_intelligence,
)
from .agents import INTELLIGENCE_WORLDS

# Language, Life and Movement are canonical Intelligence Worlds. They must not
# also appear here as cross-system capabilities. Technology, International
# Humanitarian and Multimodal remain specialist capabilities spanning worlds.
CROSS_SYSTEM_CAPABILITIES: tuple[dict[str, str], ...] = (
    {
        "id": "technology",
        "name": "Technology Intelligence",
        "purpose": (
            "Technology, compute, devices and Connectivity Intelligence, including a "
            "bounded 6G Intelligence capability without production-network claims."
        ),
    },
    {
        "id": "international_humanitarian",
        "name": "International Humanitarian Intelligence",
        "purpose": (
            "Civilian humanitarian connectivity, maps, health, aid, reunification, "
            "warnings, accessibility, safety and evidence-bounded legal/protection review."
        ),
    },
    {
        "id": "multimodal",
        "name": "Multimodal Intelligence",
        "purpose": (
            "Governed image, document, audio and sampled-video understanding through "
            "existing SMI media preparation."
        ),
    },
)

SMI_INTERNAL_CAPABILITIES: tuple[dict[str, str], ...] = (
    {
        "id": "agi_core",
        "name": "AGI Core",
        "kind": "capability_layer",
        "purpose": (
            "Routes and synthesises across specialist intelligence without claiming "
            "achieved AGI."
        ),
    },
    {
        "id": "command_intelligence",
        "name": "SMI General Intelligence Command",
        "kind": "bounded_general_intelligence_layer",
        "purpose": (
            "Nine-core path AGI → SGI → TGI → OGI → DGI → PGI → RGI → AdGI → "
            "MGI, supported by CGI, CoGI, EGI, LGI, TeGI and ReGI, with no action "
            "authority."
        ),
    },
    {
        "id": "sovereign_controls",
        "name": "SMI Master Sovereign Control Plane",
        "kind": "fail_closed_proof_based_control_plane",
        "purpose": (
            "Central technical ownership, approval, custody, audit, egress, recovery, "
            "supply-chain, emergency-halt and execution boundaries."
        ),
    },
    {
        "id": "synthetic_mind",
        "name": "Synthetic Mind Intelligence",
        "kind": "internal_organ",
        "purpose": (
            "Synthetic reasoning and provider/advisor synthesis inside the single SMI "
            "brain."
        ),
    },
    {
        "id": "biological_brain",
        "name": "Biological Brain Anatomy",
        "kind": "internal_regions",
        "purpose": (
            "Real brain-inspired routing, memory, risk, planning, integration and "
            "coordination regions."
        ),
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
        "purpose": (
            "Five automated evidence/review sections plus the Human Authority decision "
            "section."
        ),
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
        "purpose": (
            "Approved local/cloud model providers remain providers, never OAP agents or "
            "authority. Master mode permits local providers only."
        ),
    },
    {
        "id": "agents",
        "name": "Agent Registry",
        "kind": "advisory_workers",
        "purpose": (
            "Soul–Mind–Body advisory agents with one family each and bounded roles."
        ),
    },
    {
        "id": "execution",
        "name": "Living Kernel / Builder Boundary",
        "kind": "human_gated_execution",
        "purpose": (
            "Only recorded Human Authority approval can cross into consequential "
            "execution."
        ),
    },
)


def validate_smi_capabilities() -> dict[str, Any]:
    world_ids = [str(item["id"]) for item in INTELLIGENCE_WORLDS]
    cross_ids = [item["id"] for item in CROSS_SYSTEM_CAPABILITIES]
    internal_ids = [item["id"] for item in SMI_INTERNAL_CAPABILITIES]
    errors: list[str] = []
    expected_world_ids = [
        "earth",
        "language",
        "life",
        "movement",
        "civic",
        "civilisation",
        "matrix",
    ]
    if world_ids != expected_world_ids:
        errors.append("The canonical seven Intelligence Worlds are misaligned")
    if len(world_ids) != 7 or len(world_ids) != len(set(world_ids)):
        errors.append("The seven Intelligence Worlds must remain exactly seven and unique")
    if len(cross_ids) != len(set(cross_ids)):
        errors.append("Cross-system Intelligence capability IDs must be unique")
    if len(internal_ids) != len(set(internal_ids)):
        errors.append("Internal SMI capability IDs must be unique")
    if set(cross_ids) & set(world_ids):
        errors.append(
            "Cross-system capabilities must not silently become Intelligence Worlds"
        )

    reusable_registry = intelligence_capability_registry.validate_registry(tuple(world_ids))
    if not reusable_registry["passed"]:
        errors.extend(reusable_registry["errors"])

    agi = AGICore().status()
    if (
        agi["brain_count"] != 0
        or agi["independent_execute"]
        or agi["independent_approval"]
    ):
        errors.append("AGI Core escaped its bounded capability-layer role")
    if agi["agi_achieved"] or agi["general_intelligence_certified"]:
        errors.append("Architecture must not claim achieved/certified AGI without proof")

    command = CommandIntelligence().status()
    expected_command_path = (
        "sgi",
        "tgi",
        "ogi",
        "dgi",
        "pgi",
        "rgi",
        "adgi",
        "mgi",
    )
    expected_core_path = ("agi", *expected_command_path)
    expected_support = ("cgi", "cogi", "egi", "lgi", "tegi", "regi")
    if command["brain_count"] != 0:
        errors.append("Command Intelligence must not create another SMI brain")
    if command["command_path"] != expected_command_path:
        errors.append("SMI command path must preserve the locked eight command stages")
    if command["core_path"] != expected_core_path:
        errors.append("SMI core path must remain AGI plus eight command capabilities")
    if command["supporting_ids"] != expected_support:
        errors.append("SMI supporting General Intelligence set must remain the locked six")
    if command["core_general_intelligence_count"] != 9:
        errors.append("SMI must expose exactly nine core General Intelligence capabilities")
    if command["supporting_count"] != 6:
        errors.append("SMI must expose exactly six supporting General Intelligences")
    if command["independent_execute"] or command["independent_approval"]:
        errors.append("Command Intelligence must remain advisory and human-gated")
    if command["prediction_claims_fact"]:
        errors.append("PGI forecasts must never be represented as facts")
    if not command["fail_closed_resilience"]:
        errors.append("RGI must preserve fail-closed resilience")
    if command["adaptive_mutates_approved_action"]:
        errors.append("AdGI must never silently mutate an approved consequential action")
    if command["meta_decision_authority"]:
        errors.append("MGI must not become a decision authority")

    sovereign = SovereignControlPlane().status()
    if sovereign["brain_count"] != 0:
        errors.append("Sovereign controls must not create another SMI brain")
    if sovereign["independent_execute"] or sovereign["independent_approval"]:
        errors.append("Sovereign controls must not become an authority holder")
    if sovereign["external_provider_egress_default"] != "deny":
        errors.append("External provider egress must default to deny")
    if sovereign["master_mode_external_provider_egress"] != "local_only":
        errors.append("Master Sovereignty mode must restrict model providers to local")
    if sovereign["secret_export"]:
        errors.append("Sovereign controls must never enable secret export")
    if not sovereign["human_authority_final"]:
        errors.append("Human Authority must remain final")
    if sovereign["full_sovereignty_claim"] and not sovereign[
        "master_full_sovereignty_active"
    ]:
        errors.append("Full sovereignty must never be claimed without full attestation")

    specialist = {
        "earth": earth_intelligence.status(weather_ready=False),
        "language": language_intelligence.language_intelligence_status(),
        "life": life_intelligence.life_intelligence_status(),
        "movement": movement_intelligence.movement_intelligence_status(),
        "technology": technology_intelligence.technology_intelligence_status(),
        "international_humanitarian": international_humanitarian_intelligence.international_humanitarian_intelligence_status(),
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
            "reusable_intelligence_capabilities": reusable_registry["capability_count"],
            "reusable_registry_preserves_seven_worlds": reusable_registry["passed"],
            "brain_count_added_by_reusable_registry": reusable_registry["brain_count_added"],
            "brain_count_added_by_agi": agi["brain_count"],
            "brain_count_added_by_command_intelligence": command["brain_count"],
            "brain_count_added_by_sovereign_controls": sovereign["brain_count"],
            "core_general_intelligence": command[
                "core_general_intelligence_count"
            ],
            "command_stages": command["stage_count"],
            "supporting_general_intelligence": command["supporting_count"],
            "total_general_intelligence_capabilities": command[
                "total_general_intelligence_capabilities"
            ],
            "external_provider_egress_default": sovereign[
                "external_provider_egress_default"
            ],
            "master_full_sovereignty_active": sovereign[
                "master_full_sovereignty_active"
            ],
            "human_authority_final": True,
        },
    }


def smi_capability_status() -> dict[str, Any]:
    validation = validate_smi_capabilities()
    sovereign = SovereignControlPlane().status()
    command = CommandIntelligence().status()
    world_ids = tuple(str(item["id"]) for item in INTELLIGENCE_WORLDS)
    reusable_registry = intelligence_capability_registry.status(world_ids)
    return {
        "name": "Sovereign Megaverse Intelligence",
        "master_tier_name": "Master Full Sovereignty Megaverse Intelligence",
        "architecture_passed": validation["passed"],
        "validation": validation,
        "agi_core": AGICore().status(),
        "command_intelligence": command,
        "sovereign_controls": sovereign,
        "master_full_sovereignty_active": sovereign[
            "master_full_sovereignty_active"
        ],
        "core_general_intelligence_count": command[
            "core_general_intelligence_count"
        ],
        "supporting_general_intelligence_count": command["supporting_count"],
        "intelligence_worlds": tuple(dict(item) for item in INTELLIGENCE_WORLDS),
        "intelligence_capability_registry": reusable_registry,
        "cross_system_capabilities": CROSS_SYSTEM_CAPABILITIES,
        "internal_capabilities": SMI_INTERNAL_CAPABILITIES,
        "specialist_status": {
            "earth": earth_intelligence.status(weather_ready=False),
            "language": language_intelligence.language_intelligence_status(),
            "life": life_intelligence.life_intelligence_status(),
            "movement": movement_intelligence.movement_intelligence_status(),
            "technology": technology_intelligence.technology_intelligence_status(),
            "international_humanitarian": international_humanitarian_intelligence.international_humanitarian_intelligence_status(),
        },
        "human_authority_final": True,
        "independent_execution": False,
    }
