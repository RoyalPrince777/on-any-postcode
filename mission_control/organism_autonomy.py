"""Whole-organism bounded autonomy for the OAP Digital Organism.

The Digital Organism may autonomously observe its architecture and operational
readiness, detect coherence drift, review safe recovery needs and formulate
growth proposals. It never gains independent authority to approve, deploy,
spend, dispatch, publish, migrate production data or cross any other
consequential edge.
"""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from oap.smi.autonomy import SMIAutonomyEngine

from . import oap_core_autonomy, product_cores, routing
from .movement_operations import movement_schema_status
from .organism import (
    BLOCKED_CONSEQUENTIAL_ACTIONS,
    BODY_ORGANS,
    ORGANISM_SIGNAL_PATH,
    SAFE_AUTONOMY_ACTIONS,
    validate_architecture,
)
from .organism_runtime import runtime_status

AUTONOMY_MODE = "BOUNDED_AUTONOMOUS"


def _safe_snapshot(
    reader: Callable[[], dict[str, Any]], *, error_code: str
) -> dict[str, Any]:
    try:
        value = reader()
    except Exception:  # noqa: BLE001 - organism degrades to observation failure.
        return {"ready": False, "error": error_code}
    return dict(value) if isinstance(value, dict) else {"ready": False, "error": error_code}


def status() -> dict[str, Any]:
    """Return the whole-organism autonomy boundary without performing work."""
    return {
        "component": "OAP Digital Organism Autonomy",
        "mode": AUTONOMY_MODE,
        "configured": True,
        "body_organs": len(BODY_ORGANS),
        "signal_path": ORGANISM_SIGNAL_PATH,
        "safe_autonomy_actions": SAFE_AUTONOMY_ACTIONS,
        "blocked_consequential_actions": BLOCKED_CONSEQUENTIAL_ACTIONS,
        "automatic_observation": True,
        "automatic_cross_organ_coherence": True,
        "automatic_recovery_review": True,
        "automatic_growth_proposals": True,
        "independent_approval": False,
        "independent_execution": False,
        "independent_apply": False,
        "human_authority_final": True,
    }


def observe() -> dict[str, Any]:
    """Read the organism's current architecture and operational readiness."""
    architecture = validate_architecture()
    runtime = _safe_snapshot(runtime_status, error_code="runtime_status_unavailable")
    products = _safe_snapshot(
        product_cores.product_core_schema_status,
        error_code="product_core_status_unavailable",
    )
    movement = _safe_snapshot(
        movement_schema_status,
        error_code="movement_status_unavailable",
    )
    routing_state = _safe_snapshot(routing.status, error_code="routing_status_unavailable")
    oap_core = _safe_snapshot(
        oap_core_autonomy.status,
        error_code="oap_core_autonomy_status_unavailable",
    )
    smi = SMIAutonomyEngine().status()

    organs = tuple(
        {
            "id": organ["id"],
            "name": organ["name"],
            "anatomy": organ["anatomy"],
            "safe_autonomy": organ["safe_autonomy"],
            "gated_edges": organ["gated_edges"],
            "human_authority_final": organ["human_authority_final"],
        }
        for organ in BODY_ORGANS
    )
    return {
        "kind": "organism_observation",
        "architecture_ready": bool(architecture.get("passed")),
        "runtime_schema_ready": bool(runtime.get("schema_ready")),
        "runtime_worker_fresh": bool(runtime.get("worker_fresh")),
        "product_cores_ready": bool(products.get("schema_ready")),
        "movement_ready": bool(movement.get("schema_ready")),
        "routing_production_ready": bool(routing_state.get("production_ready")),
        "oap_core_autonomy_ready": bool(oap_core.get("configured")),
        "smi_autonomy_ready": bool(smi.get("configured")),
        "body_organs": organs,
        "read_only": True,
        "consequential_action": False,
    }


def coherence_review(observation: dict[str, Any] | None = None) -> dict[str, Any]:
    """Detect drift across anatomy, runtime and body-system foundations."""
    evidence = observation or observe()
    issues: list[str] = []
    if not evidence.get("architecture_ready"):
        issues.append("architecture_not_coherent")
    if not evidence.get("runtime_schema_ready"):
        issues.append("runtime_schema_not_ready")
    if not evidence.get("runtime_worker_fresh"):
        issues.append("runtime_worker_not_fresh")
    if not evidence.get("product_cores_ready"):
        issues.append("product_cores_not_ready")
    if not evidence.get("movement_ready"):
        issues.append("movement_schema_not_ready")
    if not evidence.get("routing_production_ready"):
        issues.append("routing_not_production_ready")
    if not evidence.get("oap_core_autonomy_ready"):
        issues.append("oap_core_autonomy_not_ready")
    if not evidence.get("smi_autonomy_ready"):
        issues.append("smi_autonomy_not_ready")

    escaped = [
        organ["name"]
        for organ in evidence.get("body_organs", ())
        if organ.get("human_authority_final") is not True
    ]
    if escaped:
        issues.append("organ_authority_boundary_failed")

    return {
        "kind": "organism_coherence_review",
        "coherent": not issues,
        "issues": tuple(issues[:20]),
        "body_organs_checked": len(evidence.get("body_organs", ())),
        "review_only": True,
        "consequential_action": False,
    }


def recovery_review(review: dict[str, Any] | None = None) -> dict[str, Any]:
    """Define safe organism recovery actions without applying destructive changes."""
    coherence = review or coherence_review()
    return {
        "kind": "organism_recovery_review",
        "recovery_attention": bool(coherence.get("issues")),
        "safe_actions": (
            "reobserve_organ_state",
            "recheck_cross_organ_coherence",
            "retry_nonconsequential_analysis",
            "recover_stale_runtime_lease",
        ),
        "destructive_recovery_allowed": False,
        "authority_change_allowed": False,
        "consequential_action": False,
    }


def growth_proposal(review: dict[str, Any] | None = None) -> dict[str, Any]:
    """Turn observed drift into governed organism-growth proposals."""
    coherence = review or coherence_review()
    issues = tuple(str(issue) for issue in coherence.get("issues", ()))[:20]
    proposed = tuple(f"review:{issue}" for issue in issues)
    if not proposed:
        proposed = ("maintain_current_organism_configuration",)
    return {
        "kind": "organism_growth_proposal",
        "evidence": issues,
        "proposed_actions": proposed,
        "requires_human_approval": True,
        "sandbox_required": True,
        "reversibility_required": True,
        "independent_apply": False,
        "consequential_action": False,
    }


def run_cycle() -> dict[str, Any]:
    """Run one full Digital Organism thought/review cycle."""
    observation = observe()
    coherence = coherence_review(observation)
    recovery = recovery_review(coherence)
    growth = growth_proposal(coherence)
    return {
        "kind": "digital_organism_autonomy_cycle",
        "mode": AUTONOMY_MODE,
        "observation": observation,
        "coherence": coherence,
        "recovery": recovery,
        "growth": growth,
        "human_authority_final": True,
        "independent_approval": False,
        "independent_execution": False,
        "independent_apply": False,
        "consequential_action": False,
    }
