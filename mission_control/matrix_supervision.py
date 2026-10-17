"""Read-only Tank, Dozer and Link supervisory contracts.

No worker control, network probes, repairs, delivery claims or permission grants.
Only explicitly supplied observations may be assessed.
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

ROLES = {
    "Tank": "mission_operations",
    "Dozer": "infrastructure_recovery",
    "Link": "communications_continuity",
}
ALLOWED_STATES = frozenset(("healthy", "degraded", "failed", "unknown"))


def supervision_snapshot(observations: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Classify independently sourced observations without inventing telemetry."""
    if observations is not None and not isinstance(observations, Mapping):
        raise TypeError("observations must be a mapping")
    observations = observations or {}
    if set(observations) - set(ROLES):
        raise ValueError("unknown supervisory identity")
    results: dict[str, dict[str, Any]] = {}
    for name, role in ROLES.items():
        observation = observations.get(name)
        if observation is None:
            results[name] = {"role": role, "state": "not_connected", "evidence": None}
            continue
        if not isinstance(observation, Mapping):
            raise TypeError("supervisory observation must be a mapping")
        state, evidence = observation.get("state"), observation.get("evidence")
        if state not in ALLOWED_STATES:
            raise ValueError("invalid supervisory observation state")
        if not isinstance(evidence, str) or not evidence.strip():
            raise ValueError("supervisory evidence reference required")
        results[name] = {"role": role, "state": state, "evidence": evidence.strip()}
    return {
        "mode": "read_only",
        "identities": results,
        "all_clear_proven": False,
        "runtime_verified": False,
        "delivery_confirmed": False,
        "recovery_verified": False,
        "execution_granted": False,
        "guardian_required": True,
        "human_authority_final": True,
        "full_green": False,
    }
