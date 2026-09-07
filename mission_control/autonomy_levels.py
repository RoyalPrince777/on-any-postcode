"""Canonical governed SMI autonomy levels and bounded A3/A4 runtime policy.

A1 to A7 are operating levels of the single Sovereign Megaverse Intelligence
brain. They are not agents, products, brains or separate systems. Only A3/A4 have
runtime policy here, and those actions remain pre-authorised, reversible,
audited, fail-closed and non-consequential. A5, A6 and A7 remain locked until
real evidence satisfies their gates. Human Authority remains final at every level.
"""
from __future__ import annotations

import os

from .organism_runtime import ALLOWED_JOB_TYPES

AUTONOMY_LEVELS = {
    "A1": "Manual support",
    "A2": "Guided assistance",
    "A3": "Bounded tool support",
    "A4": "Supervised autonomy",
    "A5": "Governed operational preparation",
    "A6": "Governed operational execution",
    "A7": "Certified organism-scale autonomy",
}

# A0 existed before the A1-A7 constitutional lock. Keep it only as a fail-closed
# compatibility input and map it to A1 rather than exposing a second ladder.
LEGACY_LEVEL_ALIASES = {"A0": "A1"}
DEFAULT_AUTONOMY_LEVEL = "A3"
INVALID_AUTONOMY_FALLBACK = "A2"
A3_PILOT_ACTIONS = frozenset({"RUNTIME_HEARTBEAT", "RUNTIME_HEALTH_PROBE"})
A4_WORKFLOW_ACTIONS = A3_PILOT_ACTIONS
A4_CHECKPOINT_EVERY = 3
A4_MAX_WORKFLOW_STEPS = 21
A4_REQUIRES_SUPERVISION = True
A5_ENABLED = False
A6_ENABLED = False
A7_ENABLED = False

A5_REQUIREMENTS = (
    "independent proof runner results",
    "Guardian pass",
    "Green Gate pass",
    "HRM receipts",
    "Founder approval",
    "rollback path",
    "live observability",
    "strict capability allowlist",
)
A6_REQUIREMENTS = A5_REQUIREMENTS + (
    "explicit operation-level Human Authority approval",
    "operation-specific rollback proof",
    "consequential action receipt chain",
)
A7_REQUIREMENTS = A6_REQUIREMENTS + (
    "external audit",
    "legal and compliance proof",
    "emergency halt proof",
    "public/private boundary proof",
    "constitutional review",
)

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
    """Return the configured canonical level; invalid values fail closed to A2."""
    raw = os.environ.get("OAP_AUTONOMY_LEVEL")
    if raw is None or not raw.strip():
        return DEFAULT_AUTONOMY_LEVEL
    level = raw.strip().upper()
    level = LEGACY_LEVEL_ALIASES.get(level, level)
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
    """Validate a bounded A4 workflow without granting new execution authority."""
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


def level_ladder() -> tuple[dict[str, object], ...]:
    """Return the canonical A1-A7 ladder with truthful lock state."""
    configured = configured_level()
    order = tuple(AUTONOMY_LEVELS)
    rows: list[dict[str, object]] = []
    for level in order:
        if level in {"A1", "A2"}:
            state = "supported"
        elif level == "A3":
            state = "bounded_policy_ready"
        elif level == "A4":
            state = "live_governed" if configured == "A4" else "policy_ready"
        elif level == "A5":
            state = "locked_ready_boundary"
        elif level == "A6":
            state = "future_locked"
        else:
            state = "constitutional_locked"
        rows.append(
            {
                "level": level,
                "name": AUTONOMY_LEVELS[level],
                "state": state,
                "configured": level == configured,
                "execution_authority_expanded": False,
            }
        )
    return tuple(rows)


def status() -> dict[str, object]:
    """Return autonomy policy state without claiming unobserved worker execution."""
    level = configured_level()
    pilot_actions = tuple(sorted(A3_PILOT_ACTIONS & ALLOWED_JOB_TYPES))
    a3_ready = bool(pilot_actions == tuple(sorted(A3_PILOT_ACTIONS)))
    a4_ready = bool(a3_ready and A4_WORKFLOW_ACTIONS == A3_PILOT_ACTIONS)
    return {
        "component": "OAP SMI Autonomy",
        "configured_level": level,
        "canonical_levels": level_ladder(),
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
        "a6_enabled": A6_ENABLED,
        "a7_enabled": A7_ENABLED,
        "a5_requirements": A5_REQUIREMENTS,
        "a6_requirements": A6_REQUIREMENTS,
        "a7_requirements": A7_REQUIREMENTS,
        "forbidden_domains": tuple(sorted(FORBIDDEN_DOMAINS)),
        "consequential_action_allowed": False,
        "self_permission_change_allowed": False,
        "self_constitution_change_allowed": False,
        "human_authority_final": True,
        "runtime_proof_required": True,
        "authority_moves_with_level": False,
    }
