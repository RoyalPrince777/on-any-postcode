"""Coarse public readiness projection for the implemented SMI runtime."""

from __future__ import annotations

from typing import Any

from .agents import AGENT_REGISTRY, LOCKED_FAMILY_IDS
from .db import db_status
from .organism import (
    APPROVED_STATE_PATH,
    REJECTED_STATE_PATH,
    SMI_OUTPUT_STATES,
    SMI_REGIONS,
    validate_architecture,
)

PROCESSING_CYCLE = (
    {"step": "NEXUS", "action": "Carries the incoming SP Signal"},
    {"step": "Thalamus", "action": "Filters input and redacts private metadata"},
    {"step": "Identity", "action": "Validates an active canonical identity"},
    {"step": "Permissions", "action": "Checks REQUEST_RECOMMENDATION"},
    {"step": "Hippocampus", "action": "Retrieves bounded HRM context"},
    {"step": "SMI regions", "action": "Analyse logic, meaning, space and risk"},
    {"step": "Aegis", "action": "Performs rapid deterministic threat checks"},
    {"step": "Guardian", "action": "Protects the constitutional gate"},
    {"step": "Corpus callosum", "action": "Merges internal region findings"},
    {"step": "Frontal lobe", "action": "Forms one non-execution recommendation"},
    {"step": "War Room", "action": "Simulates high-impact consequences"},
    {"step": "Human Authority", "action": "Approves or rejects with signed receipt"},
    {"step": "Living Kernel", "action": "Coordinates an approved Builder only"},
    {"step": "HRM", "action": "Records recommendation, approval and outcome"},
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
    """Return code/readiness facts without constructing or running SMI."""

    database = db_status()
    brain_storage_ready = bool(database.get("brain_runtime_initialized"))
    architecture = validate_architecture()
    active_agents = sum(agent.get("status") == "ACTIVE" for agent in AGENT_REGISTRY)
    assigned_providers = sum(bool(agent.get("provider_ids")) for agent in AGENT_REGISTRY)

    components = (
        _component(
            "NEXUS and Thalamus",
            "Implemented",
            "Ready for injected signals",
            "ready",
            "Transport and filtering only; no decision authority.",
        ),
        _component(
            "Identity and Permissions",
            "Implemented fail-closed adapters",
            "No web identity source connected",
            "waiting",
            "Uses canonical Identity records; creates no second identity store.",
        ),
        _component(
            "HRM and JOOG MEMORY",
            "Implemented with explicit SQLite schema",
            "Initialized" if brain_storage_ready else "Migration not applied",
            "ready" if brain_storage_ready else "waiting",
            "Stores input hash, reasoning trace, recommendation and outcome.",
        ),
        _component(
            "SMI biological regions",
            f"{len(SMI_REGIONS)} regions implemented",
            "Recommendation-only",
            "ready",
            "One brain; Synthetic Mind remains an internal organ.",
        ),
        _component(
            "Agent Registry",
            f"{len(AGENT_REGISTRY)} preserved agents across 7 families",
            f"{active_agents} active; no new region roles assigned",
            "ready",
            "Agents advise; they do not become organs or final authority.",
        ),
        _component(
            "Provider Router",
            "Loopback Ollama adapter and explicit router implemented",
            f"{assigned_providers} approved assignment(s)",
            "waiting" if not assigned_providers else "ready",
            "Providers power analysis only; they never become OAP agents.",
        ),
        _component(
            "Aegis and Guardian",
            "Threat checks and constitutional gate implemented",
            "Internal runtime only",
            "ready",
            "Aegis checks; Guardian protects; neither decides or executes.",
        ),
        _component(
            "War Room",
            "Reversible scenario simulation implemented",
            "Internal runtime only",
            "ready",
            "Simulates consequences; Human Authority remains final.",
        ),
        _component(
            "Human Approval",
            "Signed, expiring, action-bound, single-use level-zero receipts implemented",
            "No signing key connected to public UI",
            "waiting",
            "No approval control is exposed without verified authentication.",
        ),
        _component(
            "Living Kernel and Builder",
            "Double-gated coordination implemented",
            "Zero default Builder actions",
            "waiting",
            "The heart executes only a verified receipt and registered handler.",
        ),
        _component(
            "Audit and Evolution",
            "Hash chain, outcomes and proposal-only learning implemented",
            "Initialized" if database.get("initialized") else "Migration not applied",
            "ready" if database.get("initialized") else "waiting",
            "Evolution proposes refinements and cannot self-apply.",
        ),
    )

    activation_gates = (
        {
            "title": "Apply reviewed migrations",
            "description": (
                "Initialize the repaired audit chain and SMI runtime tables on an "
                "approved database backup."
            ),
            "status": "Requires human approval",
        },
        {
            "title": "Connect canonical Identity records",
            "description": (
                "Wire authenticated users and permissions without creating a "
                "duplicate Identity database."
            ),
            "status": "Requires human approval",
        },
        {
            "title": "Approve providers and Builder handlers",
            "description": (
                "Assign providers and bounded actions one by one after Guardian, "
                "privacy and rollback review."
            ),
            "status": "Requires human approval",
        },
    )

    return {
        "validation": architecture,
        "brain_count": 1,
        "regions": len(SMI_REGIONS),
        "families": len(LOCKED_FAMILY_IDS),
        "agents": len(AGENT_REGISTRY),
        "components": components,
        "processing_cycle": PROCESSING_CYCLE,
        "allowed_outputs": SMI_OUTPUT_STATES,
        "approved_state_path": APPROVED_STATE_PATH,
        "rejected_state_path": REJECTED_STATE_PATH,
        "activation_gates": activation_gates,
        "mode": "Recommendation-only; no public execution route",
        "human_authority": {
            "status": "Final approval required",
            "message": (
                "Runtime code is implemented, but database activation, identity "
                "wiring, providers and Builder actions remain unexecuted."
            ),
        },
    }
