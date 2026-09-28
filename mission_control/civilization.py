"""Canonical first-party OAP Living Digital Civilization registry.

This module is deliberately read-only. It defines the architecture, first-party
authority boundary, operating loop and evidence states for OAP World. It does
not execute, deploy, migrate, publish, transfer value, or grant permissions.
"""

from __future__ import annotations

from typing import Any

SYSTEM_LAYERS: tuple[dict[str, Any], ...] = (
    {
        "id": "oap_kernel",
        "name": "OAP Kernel",
        "role": "technical_runtime",
        "responsibility": "Lifecycle, service registry, permissions boundary, STOP hooks and recoverable platform primitives.",
        "authority": "bounded_runtime",
    },
    {
        "id": "living_kernel",
        "name": "Living Kernel",
        "role": "adaptive_runtime",
        "responsibility": "World state, dependency health, event fabric, recovery, evidence and approved action coordination.",
        "authority": "human_approval_required_for_consequential_execution",
    },
    {
        "id": "civilization_kernel",
        "name": "Civilization Kernel",
        "role": "cross_domain_coordination",
        "responsibility": "Keeps people, place, movement, communication, economy, culture, institutions, resources and safety coherent.",
        "authority": "coordination_only",
    },
    {
        "id": "smi",
        "name": "SMI",
        "role": "brain",
        "responsibility": "Interprets intent, reasons over OAP state and proposes governed actions.",
        "authority": "recommendation_and_bounded_orchestration",
    },
    {
        "id": "civilization_intelligence",
        "name": "Civilization Intelligence",
        "role": "world_model",
        "responsibility": "Models cross-domain relationships, dependencies and consequences over time.",
        "authority": "analysis_only",
    },
    {
        "id": "oap_world",
        "name": "OAP World",
        "role": "human_surface",
        "responsibility": "Presents governed first-party services to people through public and private surfaces.",
        "authority": "user_facing_surface",
    },
)

CIVILIZATION_DOMAINS: tuple[dict[str, str], ...] = (
    {"id": "people", "name": "People & Community", "owner": "My World / Family Tree / Community"},
    {"id": "place", "name": "Territory & Place", "owner": "On Any Place / OAP World Graph"},
    {"id": "movement", "name": "Movement", "owner": "Movement / Routing / Delivery"},
    {"id": "communication", "name": "Communication", "owner": "The Link / Link Up / Link Call"},
    {"id": "economy", "name": "Economy", "owner": "Market / SIKA / Work & Wealth"},
    {"id": "culture", "name": "Culture", "owner": "Music / Media / TV / Live / Records"},
    {"id": "institutions", "name": "Institutions & Governance", "owner": "Identity / Registry / Global Affairs"},
    {"id": "environment", "name": "Environment & Resources", "owner": "Weather / Infrastructure / Resource Intelligence"},
    {"id": "safety", "name": "Safety & Resilience", "owner": "Guardian / Aegis / Recovery"},
)

LIVING_LOOP: tuple[str, ...] = (
    "SENSE",
    "VERIFY",
    "UNDERSTAND",
    "COORDINATE",
    "AUTHORIZE",
    "ACT",
    "OBSERVE",
    "LEARN",
    "RECOVER",
)

FIRST_PARTY_AUTHORITY: tuple[str, ...] = (
    "canonical_identity",
    "canonical_ids",
    "data_relationships",
    "policy",
    "permissions",
    "decision_receipts",
    "audit",
    "recovery",
    "user_experience",
)

REPLACEABLE_SUPPLIERS: tuple[str, ...] = (
    "compute_hosting",
    "network_access",
    "external_source_data",
    "regulated_payment_rails",
    "external_model_inference",
    "device_hardware",
    "licensed_content",
    "manufacturing_and_fulfilment",
)

PROTOCOL_GATES: tuple[dict[str, str], ...] = (
    {"percent": "25", "name": "Rollback", "rule": "Known-good rollback or recovery path exists before progression."},
    {"percent": "50", "name": "Runtime Guard", "rule": "Runtime boundaries, permissions and failure isolation are verified."},
    {"percent": "75", "name": "Aegis", "rule": "Safety, privacy, provenance and no-fake-green checks pass."},
    {"percent": "100", "name": "Green Gate + Founder Final", "rule": "Required live evidence exists and Human Authority remains final."},
)


def validate_civilization_system() -> dict[str, Any]:
    errors: list[str] = []
    layer_ids = [layer["id"] for layer in SYSTEM_LAYERS]
    domain_ids = [domain["id"] for domain in CIVILIZATION_DOMAINS]

    if len(layer_ids) != len(set(layer_ids)):
        errors.append("Duplicate civilization layer IDs.")
    if len(domain_ids) != len(set(domain_ids)):
        errors.append("Duplicate civilization domain IDs.")
    if layer_ids.count("smi") != 1:
        errors.append("SMI must remain one canonical brain layer.")
    if "living_kernel" not in layer_ids:
        errors.append("Living Kernel is required.")
    if "civilization_kernel" not in layer_ids:
        errors.append("Civilization Kernel is required.")
    if tuple(gate["percent"] for gate in PROTOCOL_GATES) != ("25", "50", "75", "100"):
        errors.append("Four-gate protocol order changed.")
    if LIVING_LOOP[-1] != "RECOVER":
        errors.append("Living loop must end with recovery.")

    return {
        "passed": not errors,
        "errors": errors,
        "checks": {
            "layers": len(SYSTEM_LAYERS),
            "domains": len(CIVILIZATION_DOMAINS),
            "one_brain": layer_ids.count("smi") == 1,
            "human_authority_final": True,
            "no_fake_green": True,
            "external_suppliers_replaceable": True,
        },
    }


def get_civilization_status() -> dict[str, Any]:
    validation = validate_civilization_system()
    return {
        "name": "OAP Living Digital Civilization System",
        "mode": "first_party_authority",
        "status": "architecture_protocol_defined",
        "operational_green": False,
        "operational_green_reason": "Each capability remains evidence-gated independently; architecture definition is not live-runtime proof.",
        "layers": SYSTEM_LAYERS,
        "domains": CIVILIZATION_DOMAINS,
        "living_loop": LIVING_LOOP,
        "first_party_authority": FIRST_PARTY_AUTHORITY,
        "replaceable_suppliers": REPLACEABLE_SUPPLIERS,
        "protocol_gates": PROTOCOL_GATES,
        "validation": validation,
        "governance": {
            "proof_before_green": True,
            "human_approval_before_consequential_action": True,
            "stop_available": True,
            "recovery_required": True,
            "public_private_separation": True,
        },
    }
