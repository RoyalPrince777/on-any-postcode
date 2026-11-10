"""Read-only Independent Oversight for the Observation Ladder Level 07.

This module audits explicit evidence supplied by callers. It does not collect data,
grant authority, certify itself, mutate production, approve recommendations or
execute consequential actions.
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

OVERSIGHT_DIMENSIONS = (
    "truth",
    "authority",
    "privacy",
    "security",
    "bias",
    "evidence",
    "reversibility",
)

_ALLOWED_STATES = {"proven", "conflicting", "stale", "unavailable", "unknown"}


def status() -> dict[str, Any]:
    """Return the fixed authority boundary for Level 07 oversight."""
    return {
        "component": "Independent Oversight",
        "observation_ladder_level": 7,
        "mode": "READ_ONLY_ASSURANCE",
        "dimensions": OVERSIGHT_DIMENSIONS,
        "independent_execution": False,
        "independent_approval": False,
        "permission_change_allowed": False,
        "production_write": False,
        "self_certification_allowed": False,
        "human_authority_final": True,
    }


def review(evidence: Mapping[str, object]) -> dict[str, Any]:
    """Audit explicit evidence against the seven Level 07 dimensions."""
    checks: list[dict[str, object]] = []
    blocking: list[str] = []
    unresolved: list[str] = []

    for dimension in OVERSIGHT_DIMENSIONS:
        value = evidence.get(dimension)
        if value is True:
            result = "proven"
        elif value is False:
            result = "failed"
            blocking.append(dimension)
        else:
            result = "unknown"
            unresolved.append(dimension)
        checks.append({"dimension": dimension, "result": result})

    raw_state = str(evidence.get("evidence_state", "unknown")).strip().casefold()
    evidence_state = raw_state if raw_state in _ALLOWED_STATES else "unknown"
    if evidence_state != "proven":
        unresolved.append("evidence_state")

    green_candidate = not blocking and not unresolved
    signal = "green" if green_candidate else ("red" if blocking else "yellow")

    return {
        "kind": "smi_independent_oversight_review",
        "checks": tuple(checks),
        "blocking_dimensions": tuple(blocking),
        "unresolved_dimensions": tuple(unresolved),
        "evidence_state": evidence_state,
        "green_candidate": green_candidate,
        "signal": signal,
        "review_only": True,
        "execution_granted": False,
        "approval_granted": False,
        "self_certification": False,
        "human_authority_final": True,
    }