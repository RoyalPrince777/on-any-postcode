"""Governed OAP autonomy levels and bounded A3/A4 runtime policy.

A3 executes only pre-authorised, reversible, audited and fail-closed runtime
maintenance actions. A4 may keep those same bounded actions operating through
longer supervised workflows, but it does not widen the action allowlist or grant
consequential authority. Human Authority remains final and A5 stays locked.
"""
from __future__ import annotations

import os

from .organism_runtime import ALLOWED_JOB_TYPES

AUTONOMY_LEVELS = {
    "A0": "Respond only",
    "A1": "Assist with bounded tools",
    "A2": "Observe, reason and propose",
    "A3": "Execute pre-authorised reversible bounded actions",
    "A4": "Operate longer supervised bounded workflows",
    "A5": "Broad autonomous operation",
}

DEFAULT_AUTONOMY_LEVEL = "A3"
INVALID_AUTONOMY_FALLBACK = "A2"
A3_PILOT_ACTIONS = frozenset({"RUNTIME_HEARTBEAT", "RUNTIME_HEALTH_PROBE"})
A4_WORKFLOW_ACTIONS = A3_PILOT_ACTIONS
A4_CHECKPOINT_EVERY = 3
A4_MAX_WORKFLOW_STEPS = 21
A4_REQUIRES_SUPERVISION = True
A5_ENABLED = False
FORBIDDEN_DOMAINS = frozenset(
    {
        "money_or_value_transfer",
        "destructive_data_change",
        "production_database_migration",
        "identity_or_permission_change",
        "security_or_auth_change",
        "real_world_dispatch",
        "public_publishing",
        "unreviewed_code_deploy",
        "self_permission_change",
        "self_constitution_change",
    }
)
# Compatibility alias retained for existing callers/tests.
A3_FORBIDDEN_DOMAINS = FORBIDDEN_DOMAINS


def configured_level() -> str:
    """Default to bounded A3; invalid explicit values fail closed to A2."""
    raw = os.environ.get("OAP_AUTONOMY_LEVEL")
    if raw is None or not raw.strip():
        return DEFAULT_AUTONOMY_LEVEL
    level = raw.strip().upper()
    return level if level in AUTONOMY_LEVELS else INVALID_AUTONOMY_FALLBACK


def evaluate_runtime_job(job_type: str) -> dict[str, object]:
    """Evaluate one runtime action under the configured A3/A4 policy."""
    normalized = str(job_type).strip().upper()
    level = configured_level()
    allowlisted = normalized in A3_PILOT_ACTIONS and normalized in ALLOWED_JOB_TYPES
    bounded_level = level in {"A3", "A4"}
    allowed = bounded_level and allowlisted
    if allowed:
        reason = "allowed"
    elif level not in {"A3", "A4"}:
        reason = "bounded_runtime_autonomy_not_enabled"
    else:
        reason = "action_not_bounded_allowlisted"
    return {
        "configured_level": level,
        "requested_level": level,
        "action_type": normalized,
        "allowed": allowed,
        "reason": reason,
        "pre_authorised": allowlisted,
        "reversible_required": True,
        "audit_required": True,
        "fail_closed": True,
        "supervision_required": level == "A4",
        "a4_workflow_eligible": bool(level == "A4" and allowlisted),
        "consequential_action_allowed": False,
        "human_authority_final": True,
    }


def evaluate_a3_runtime_job(job_type: str) -> dict[str, object]:
    """Compatibility wrapper for callers that still use the A3 function name."""
    decision = evaluate_runtime_job(job_type)
    if decision["allowed"]:
        reason = "allowed"
    elif configured_level() not in {"A3", "A4"}:
        reason = "a3_not_enabled"
    else:
        reason = "action_not_a3_allowlisted"
    return {**decision, "requested_level": "A3", "reason": reason}


def evaluate_a4_workflow(action_types: object, *, supervised: bool = True) -> dict[str, object]:
    """Validate a bounded A4 workflow without granting new execution authority.

    A workflow may contain at most 21 steps and every step must already be an A3
    reversible runtime action. The function is deliberately policy-only: the
    runtime remains responsible for execution, receipts and failure handling.
    """
    if isinstance(action_types, str):
        actions = (action_types.strip().upper(),)
    else:
        try:
            actions = tuple(str(item).strip().upper() for item in action_types)  # type: ignore[arg-type]
        except TypeError:
            actions = ()
    actions = tuple(item for item in actions if item)
    level = configured_level()
    within_size = 1 <= len(actions) <= A4_MAX_WORKFLOW_STEPS
    all_allowlisted = bool(actions) and all(
        item in A4_WORKFLOW_ACTIONS and item in ALLOWED_JOB_TYPES for item in actions
    )
    allowed = bool(
        level == "A4"
        and supervised is True
        and within_size
        and all_allowlisted
    )
    if allowed:
        reason = "allowed"
    elif level != "A4":
        reason = "a4_not_enabled"
    elif supervised is not True:
        reason = "a4_supervision_required"
    elif not within_size:
        reason = "a4_workflow_size_out_of_bounds"
    else:
        reason = "a4_workflow_contains_unapproved_action"
    return {
        "configured_level": level,
        "requested_level": "A4",
        "allowed": allowed,
        "reason": reason,
        "steps": actions,
        "step_count": len(actions),
        "max_steps": A4_MAX_WORKFLOW_STEPS,
        "checkpoint_every": A4_CHECKPOINT_EVERY,
        "supervision_required": True,
        "audit_required": True,
        "reversible_required": True,
        "dynamic_permission_expansion_allowed": False,
        "consequential_action_allowed": False,
        "human_authority_final": True,
    }


def status() -> dict[str, object]:
    """Return autonomy policy state without claiming unobserved worker execution."""
    level = configured_level()
    pilot_actions = tuple(sorted(A3_PILOT_ACTIONS & ALLOWED_JOB_TYPES))
    a3_ready = bool(pilot_actions == tuple(sorted(A3_PILOT_ACTIONS)))
    a4_ready = bool(a3_ready and A4_WORKFLOW_ACTIONS == A3_PILOT_ACTIONS)
    return {
        "component": "OAP Autonomy",
        "configured_level": level,
        "a3_policy_ready": a3_ready,
        "a3_execution_enabled": level in {"A3", "A4"},
        "a3_pilot_actions": pilot_actions,
        "a4_policy_ready": a4_ready,
        "a4_enabled": level == "A4" and a4_ready,
        "a4_workflow_actions": tuple(sorted(A4_WORKFLOW_ACTIONS)),
        "a4_checkpoint_every": A4_CHECKPOINT_EVERY,
        "a4_max_workflow_steps": A4_MAX_WORKFLOW_STEPS,
        "a4_supervision_required": A4_REQUIRES_SUPERVISION,
        "a4_expands_action_authority": False,
        "a5_enabled": A5_ENABLED,
        "forbidden_domains": tuple(sorted(FORBIDDEN_DOMAINS)),
        "consequential_action_allowed": False,
        "self_permission_change_allowed": False,
        "human_authority_final": True,
        "runtime_proof_required": True,
    }
