"""Governed OAP autonomy levels and the bounded A3 runtime policy.

A3 means a pre-authorised, reversible, audited and fail-closed action may run
without a fresh Human Authority approval for every individual occurrence.
It never grants broader decision authority. Consequential actions remain on the
Human Authority -> Living Kernel -> Builder path.
"""
from __future__ import annotations

import os

from .organism_runtime import ALLOWED_JOB_TYPES

AUTONOMY_LEVELS = {
    "A0": "Respond only",
    "A1": "Assist with bounded tools",
    "A2": "Observe, reason and propose",
    "A3": "Execute pre-authorised reversible bounded actions",
    "A4": "Operate longer supervised workflows",
    "A5": "Broad autonomous operation",
}

DEFAULT_AUTONOMY_LEVEL = "A3"
INVALID_AUTONOMY_FALLBACK = "A2"
A3_PILOT_ACTIONS = frozenset({"RUNTIME_HEARTBEAT", "RUNTIME_HEALTH_PROBE"})
A3_FORBIDDEN_DOMAINS = frozenset(
    {
        "money_or_value_transfer",
        "destructive_data_change",
        "production_database_migration",
        "identity_or_permission_change",
        "security_or_auth_change",
        "real_world_dispatch",
        "public_publishing",
        "unreviewed_code_deploy",
    }
)


def configured_level() -> str:
    """Default to bounded A3; invalid explicit values fail closed to A2."""
    raw = os.environ.get("OAP_AUTONOMY_LEVEL")
    if raw is None or not raw.strip():
        return DEFAULT_AUTONOMY_LEVEL
    level = raw.strip().upper()
    return level if level in AUTONOMY_LEVELS else INVALID_AUTONOMY_FALLBACK


def evaluate_a3_runtime_job(job_type: str) -> dict[str, object]:
    """Evaluate one runtime job against the A3 allowlist and hard boundaries."""
    normalized = str(job_type).strip().upper()
    level = configured_level()
    allowlisted = normalized in A3_PILOT_ACTIONS and normalized in ALLOWED_JOB_TYPES
    allowed = level == "A3" and allowlisted
    reason = "allowed" if allowed else (
        "a3_not_enabled" if level != "A3" else "action_not_a3_allowlisted"
    )
    return {
        "configured_level": level,
        "requested_level": "A3",
        "action_type": normalized,
        "allowed": allowed,
        "reason": reason,
        "pre_authorised": allowlisted,
        "reversible_required": True,
        "audit_required": True,
        "fail_closed": True,
        "consequential_action_allowed": False,
        "human_authority_final": True,
    }


def status() -> dict[str, object]:
    """Return the static A3 policy state without claiming live worker proof."""
    level = configured_level()
    pilot_actions = tuple(sorted(A3_PILOT_ACTIONS & ALLOWED_JOB_TYPES))
    return {
        "component": "OAP Autonomy",
        "configured_level": level,
        "a3_policy_ready": bool(pilot_actions == tuple(sorted(A3_PILOT_ACTIONS))),
        "a3_execution_enabled": level == "A3",
        "a3_pilot_actions": pilot_actions,
        "a4_enabled": False,
        "a5_enabled": False,
        "forbidden_domains": tuple(sorted(A3_FORBIDDEN_DOMAINS)),
        "consequential_action_allowed": False,
        "human_authority_final": True,
        "runtime_proof_required": True,
    }
