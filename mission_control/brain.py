"""Truthful readiness projection for the implemented OAP SMI brain."""

from __future__ import annotations

from typing import Any

from . import autonomy_levels, intelligence_lenses
from .agents import AGENT_REGISTRY, LOCKED_FAMILY_IDS
from .database import db_status
from .organism import (
    APPROVED_STATE_PATH,
    REJECTED_STATE_PATH,
    SMI_OUTPUT_STATES,
    SMI_REGIONS,
    validate_architecture,
)

PROCESSING_CYCLE = (
    {"step": "NEXUS", "action": "Carries the incoming SP Signal"},
    {"step": "Thalamus", "action": "Filters input and redacts private OAP Data"},
    {"step": "Identity", "action": "Validates the signed private identity"},
    {"step": "Permissions", "action": "Checks REQUEST_RECOMMENDATION and Founder boundaries"},
    {"step": "Hippocampus", "action": "Retrieves bounded governed HRM context"},
    {"step": "Intelligence Lens Router", "action": "Selects the smallest sufficient analysis lenses"},
    {"step": "OAP Intelligence regions", "action": "Analyse logic, meaning, space and risk"},
    {"step": "Aegis", "action": "Performs rapid deterministic threat checks"},
    {"step": "Guardian", "action": "Protects the constitutional gate"},
    {"step": "Corpus callosum", "action": "Merges internal region findings"},
    {"step": "Frontal lobe", "action": "Forms one non-execution recommendation"},
    {"step": "War Room", "action": "Reviews high-impact consequences and proof"},
    {"step": "Judgement", "action": "Recommends PASS, CONDITIONAL, HOLD or REJECT"},
    {"step": "Human Authority", "action": "Approves or rejects where approval is required"},
    {"step": "Living Kernel", "action": "Coordinates only an explicitly approved bounded Builder action"},
    {"step": "HRM", "action": "Records recommendation, approval, outcome and lesson"},
)


def _component(
    name: str,
    implementation: str,
    runtime: str,
    state: str,
    boundary: str,
) -> dict[str, str]:
    return {
        "name": name,
        "implementation": implementation,
        "runtime": runtime,
        "state": state,
        "boundary": boundary,
    }


def get_public_brain_status() -> dict[str, Any]:
    """Return code/readiness facts without pretending unobserved runtime is green."""

    database = db_status()
    brain_storage_ready = bool(database.get("brain_runtime_initialized"))
    architecture = validate_architecture()
    active_agents = sum(agent.get("status") == "ACTIVE" for agent in AGENT_REGISTRY)
    assigned_providers = sum(bool(agent.get("provider_ids")) for agent in AGENT_REGISTRY)
    autonomy = autonomy_levels.status()

    components = (
        _component(
            "NEXUS and Thalamus",
            "Implemented",
            "Ready for governed signals",
            "ready",
            "Transport and filtering only; no decision authority.",
        ),
        _component(
            "Identity and Permissions",
            "Founder-only Mission Control decorators, signed-session identity and permission checks implemented",
            "Private routes are wired; authenticated interaction proof remains a runtime checkpoint",
            "ready",
            "Private capability fails closed; no second identity authority is created.",
        ),
        _component(
            "HRM and governed memory",
            "Conversation persistence, canonical memory orchestration, audit fields and receipt paths implemented",
            "Local brain schema initialized" if brain_storage_ready else "Production paths exist; local brain schema migration remains separate",
            "ready" if brain_storage_ready else "waiting",
            "Memory records evidence and outcomes; it cannot manufacture proof or approval.",
        ),
        _component(
            "OAP Intelligence biological regions",
            f"{len(SMI_REGIONS)} regions implemented",
            "Recommendation-only",
            "ready",
            "One SMI brain; biological regions are organs, not competing brains.",
        ),
        _component(
            "Intelligence Lenses",
            f"{len(intelligence_lenses.FULL_LENS_IDS)} governed lenses with {len(intelligence_lenses.CORE_LENS_IDS)} core decision lenses",
            "Callable from Personal SMI through the Intelligence router",
            "ready",
            "Lenses analyse; they are not agents and cannot award execution authority.",
        ),
        _component(
            "Agent Registry",
            f"{len(AGENT_REGISTRY)} passports across {len(LOCKED_FAMILY_IDS)} families",
            f"{active_agents} active; {assigned_providers} explicit provider assignment(s)",
            "ready" if architecture["checks"].get("registry_ready_for_activation") else "waiting",
            "Agents advise within registered roles; providers never become OAP agents.",
        ),
        _component(
            "Inference Provider Boundary",
            "Replaceable OAP inference gateway, local-first compatibility and grounded provider wrapper implemented",
            "Provider health is verified by the private chat health path, not by this static page",
            "ready",
            "Provider is plumbing only; SMI identity, memory, governance and authority remain OAP-owned.",
        ),
        _component(
            "Aegis and Guardian",
            "Threat checks, privacy boundary and constitutional fail-closed gate implemented",
            "Private runtime boundary wired",
            "ready",
            "Aegis checks; Guardian protects; neither self-approves or executes.",
        ),
        _component(
            "War Room and Evidence",
            "Evidence runner, scenarios, SWOT, alignment, recovery and proof surfaces implemented",
            "Founder-only routes wired; fresh external evidence must still be supplied where required",
            "ready",
            "War Room analyses and prepares; it cannot secretly execute.",
        ),
        _component(
            "Judgement and Human Approval",
            "Private Judgement route and signed decision/receipt path implemented",
            "Production approval receipt evidence remains a live proof gate",
            "waiting",
            "Only Human Authority may cross approval gates; recommendation never equals approval.",
        ),
        _component(
            "Autonomy A1-A7",
            "Canonical operating-level policy implemented",
            f"Configured {autonomy['configured_level']}; A5={autonomy['a5_enabled']}, A6={autonomy['a6_enabled']}, A7={autonomy['a7_enabled']}",
            "ready",
            "Higher levels expand governed capability only. Authority never moves from Human Authority.",
        ),
        _component(
            "Living Kernel and Builder",
            "Double-gated coordination boundary implemented",
            "Consequential execution remains locked pending receipts, rollback and explicit approval",
            "waiting",
            "Living Kernel may coordinate only a verified, allowed and approved action.",
        ),
        _component(
            "Audit, Learning and Evolution",
            "Hash-chain audit, outcomes and proposal-only learning implemented",
            "Initialized" if database.get("initialized") else "Local migration state not proven here",
            "ready" if database.get("initialized") else "waiting",
            "Learning may propose refinements; it cannot self-apply, self-promote or rewrite the constitution.",
        ),
    )

    activation_gates = (
        {
            "title": "Prove authenticated Founder Intelligence interaction",
            "description": "Capture an end-to-end signed Founder chat command, governed response, persistence and safe lens-route metadata.",
            "status": "Runtime proof required",
        },
        {
            "title": "Prove production HRM and Green Gate receipt chain",
            "description": "Capture durable recommendation, approval and outcome receipts and show Green Gate consuming real evidence rather than static labels.",
            "status": "Runtime proof required",
        },
        {
            "title": "Prove rollback, recovery and observability",
            "description": "Capture failure-path, safe resume, fresh health/error telemetry and operation-specific rollback before any A6 capability.",
            "status": "Runtime proof required",
        },
        {
            "title": "Keep A5-A7 locked until their gates pass",
            "description": "A5 requires proof/Guardian/Green Gate/HRM/Founder/rollback/observability/allowlist. A6 adds operation-level proof. A7 adds external audit, legal/compliance, emergency halt, boundary proof and constitutional review.",
            "status": "Constitutional lock",
        },
    )

    return {
        "validation": architecture,
        "brain_count": 1,
        "regions": len(SMI_REGIONS),
        "families": len(LOCKED_FAMILY_IDS),
        "agents": len(AGENT_REGISTRY),
        "intelligence_lenses": len(intelligence_lenses.FULL_LENS_IDS),
        "core_intelligence_lenses": len(intelligence_lenses.CORE_LENS_IDS),
        "autonomy": autonomy,
        "components": components,
        "processing_cycle": PROCESSING_CYCLE,
        "allowed_outputs": SMI_OUTPUT_STATES,
        "approved_state_path": APPROVED_STATE_PATH,
        "rejected_state_path": REJECTED_STATE_PATH,
        "activation_gates": activation_gates,
        "mode": "Founder-only governed intelligence; consequential execution remains locked",
        "truth_light_rule": "Only Truth Intelligence plus Evidence Intelligence can support green.",
        "human_authority": {
            "status": "Final authority retained",
            "message": (
                "Private identity, chat, intelligence routing and Judgement code are wired. "
                "Runtime receipt, Green Gate, rollback and observability proof still gate higher autonomy."
            ),
        },
    }
