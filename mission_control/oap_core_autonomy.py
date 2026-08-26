"""Bounded autonomous observation and improvement review for OAP CORE.

OAP CORE may observe, compare, detect drift and generate improvement proposals
without waiting for a chat request. It never receives independent authority to
publish, deploy, spend, dispatch, change permissions, migrate production data,
activate carriers or expose precise location.
"""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from . import postgres_db, routing
from .movement_operations import movement_schema_status
from .organism_runtime import runtime_status
from .product_cores import product_core_schema_status

AUTONOMY_MODE = "BOUNDED_AUTONOMOUS"
BLOCKED_ACTIONS = (
    "deploy",
    "publish_external",
    "payment_capture",
    "money_transfer",
    "driver_dispatch",
    "permission_change",
    "role_change",
    "production_migration",
    "esim_activation",
    "carrier_switch",
    "public_precise_tracking",
    "self_apply_improvement",
)


def status() -> dict[str, Any]:
    """Return the immutable authority boundary for autonomous OAP CORE work."""
    return {
        "component": "OAP CORE Autonomy",
        "mode": AUTONOMY_MODE,
        "configured": True,
        "automatic_observation": True,
        "automatic_coherence_review": True,
        "automatic_recovery_review": True,
        "automatic_improvement_proposals": True,
        "independent_execution": False,
        "independent_apply": False,
        "human_authority_final": True,
        "blocked_actions": list(BLOCKED_ACTIONS),
    }


def _safe_snapshot(reader: Callable[[], dict[str, Any]], *, error_code: str) -> dict[str, Any]:
    try:
        value = reader()
    except Exception:  # noqa: BLE001 - autonomy degrades to observation failure.
        return {"ready": False, "error": error_code}
    return dict(value) if isinstance(value, dict) else {"ready": False, "error": error_code}


def observe() -> dict[str, Any]:
    """Collect bounded read-only operational evidence."""
    database = _safe_snapshot(postgres_db.postgres_status, error_code="postgres_status_unavailable")
    runtime = _safe_snapshot(runtime_status, error_code="runtime_status_unavailable")
    return {
        "kind": "oap_core_observation",
        "database_ready": bool(database.get("initialized")),
        "runtime_ready": bool(runtime.get("ready")),
        "runtime_schema_ready": bool(runtime.get("schema_ready")),
        "runtime_worker_fresh": bool(runtime.get("worker_fresh")),
        "retry_jobs": int(runtime.get("retry", 0) or 0),
        "dead_letter_jobs": int(runtime.get("dead_letter", 0) or 0),
        "read_only": True,
        "consequential_action": False,
    }


def coherence_review() -> dict[str, Any]:
    """Compare core runtime, product, Movement and routing readiness without changing them."""
    runtime = _safe_snapshot(runtime_status, error_code="runtime_status_unavailable")
    movement = _safe_snapshot(movement_schema_status, error_code="movement_status_unavailable")
    product_cores = _safe_snapshot(
        product_core_schema_status,
        error_code="product_core_status_unavailable",
    )
    routing_state = _safe_snapshot(routing.status, error_code="routing_status_unavailable")

    issues: list[str] = []
    if not runtime.get("schema_ready"):
        issues.append("runtime_schema_not_ready")
    if not runtime.get("worker_fresh"):
        issues.append("runtime_worker_not_fresh")
    if int(runtime.get("dead_letter", 0) or 0) > 0:
        issues.append("runtime_dead_letters_present")
    if not movement.get("schema_ready"):
        issues.append("movement_schema_not_ready")
    if not product_cores.get("schema_ready"):
        issues.append("product_core_schema_not_ready")
    if routing_state.get("provider_tier") == "production_candidate" and not routing_state.get("production_ready"):
        issues.append("routing_candidate_not_promoted")

    return {
        "kind": "oap_core_coherence_review",
        "coherent": not issues,
        "issues": issues[:12],
        "review_only": True,
        "consequential_action": False,
    }


def recovery_review(observation: dict[str, Any] | None = None) -> dict[str, Any]:
    """Recommend recovery attention; stale-lease recovery remains runtime-bounded."""
    evidence = observation or observe()
    retry_jobs = int(evidence.get("retry_jobs", 0) or 0)
    dead_letters = int(evidence.get("dead_letter_jobs", 0) or 0)
    return {
        "kind": "oap_core_recovery_review",
        "recovery_attention": bool(retry_jobs or dead_letters),
        "retry_jobs": retry_jobs,
        "dead_letter_jobs": dead_letters,
        "automatic_lease_recovery_allowed": True,
        "destructive_recovery_allowed": False,
        "consequential_action": False,
    }


def improvement_proposal(review: dict[str, Any] | None = None) -> dict[str, Any]:
    """Generate a bounded proposal; application always remains a Human action."""
    coherence = review or coherence_review()
    issues = [str(item) for item in coherence.get("issues", [])][:12]
    proposed = [f"review:{issue}" for issue in issues] or ["maintain_current_configuration"]
    return {
        "kind": "oap_core_improvement_proposal",
        "evidence": issues,
        "proposed_actions": proposed,
        "requires_human_approval": True,
        "sandbox_required": True,
        "reversibility_required": True,
        "independent_apply": False,
        "consequential_action": False,
    }


def run_cycle() -> dict[str, Any]:
    """Run one autonomous OAP CORE thought cycle with no consequential authority."""
    observation = observe()
    coherence = coherence_review()
    recovery = recovery_review(observation)
    proposal = improvement_proposal(coherence)
    return {
        "kind": "oap_core_autonomy_cycle",
        "mode": AUTONOMY_MODE,
        "observation": observation,
        "coherence": coherence,
        "recovery": recovery,
        "proposal": proposal,
        "human_authority_final": True,
        "independent_execution": False,
        "consequential_action": False,
    }