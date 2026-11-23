"""Founder-supplied, offline-only Matrix privacy checks.

These are deterministic advisory checks tagged with the seven registered Matrix
roles, NOT independent agent processes and NOT a device or network scanner.
No input is persisted, transmitted, or used to change permissions.
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from . import matrix_signal_bus

_ALLOWED_FIELDS = {
    "unknown_tracker_alert": "bool",
    "unrecognised_app_count": "count",
    "location_permission_count": "count",
    "microphone_permission_count": "count",
    "camera_permission_count": "count",
    "security_updates_current": "bool",
    "account_mfa_enabled": "bool",
}
_ROLES = (
    "Neo", "Morpheus", "Trinity", "Oracle", "Architect", "Keymaker", "Seraph",
)


def _validated(snapshot: Mapping[str, object]) -> dict[str, object]:
    if not isinstance(snapshot, Mapping):
        raise TypeError("A bounded device-facts mapping is required")
    unknown = set(snapshot) - set(_ALLOWED_FIELDS)
    if unknown:
        raise ValueError("Unknown fact fields are not accepted")
    result: dict[str, object] = {}
    for key, kind in _ALLOWED_FIELDS.items():
        value = snapshot.get(key)
        if value is None:
            result[key] = None
        elif kind == "bool":
            if type(value) is not bool:
                raise ValueError("Boolean device fact required: " + key)
            result[key] = value
        else:
            if type(value) is not int or not 0 <= value <= 1000:
                raise ValueError("Bounded non-negative count required: " + key)
            result[key] = value
    return result


def _result(agent: str, status: str, finding: str) -> dict[str, str]:
    return {"agent": agent, "status": status, "finding": finding,
            "proof": "founder_supplied_facts_only"}


def _count_status(value: object) -> str:
    if value is None:
        return "unknown"
    return "review" if value > 0 else "no_flag"


def review_founder_device_facts(snapshot: Mapping[str, object]) -> dict[str, Any]:
    """Review provided observations without performing any device-side action.

    Input must contain only the allowlisted coarse facts. 'No flag' only means
    the supplied values do not trigger a rule, never that tracking is absent.
    """
    if matrix_signal_bus.registered_matrix_names() != _ROLES:
        raise RuntimeError("Canonical seven-role Matrix registry mismatch")
    f = _validated(snapshot)
    alert = f["unknown_tracker_alert"]
    neo = _result(
        "Neo",
        "unknown" if alert is None else "review" if alert else "no_flag",
        "Review the system's unknown-tracker alert and physical safety guidance."
        if alert else "No positive tracker alert was supplied; this is not a scan."
    )

    observed = sum(value is not None for value in f.values())
    morpheus = _result(
        "Morpheus", "unknown" if observed == 0 else "no_flag",
        "No device evidence supplied." if observed == 0
        else "The facts are self-reported and not independently verified."
    )

    app_status = _count_status(f["unrecognised_app_count"])
    architect = _result(
        "Architect", app_status,
        "Inspect unrecognised apps before uninstalling or changing anything."
        if app_status == "review" else "App inventory not independently checked."
    )

    mfa = f["account_mfa_enabled"]
    keymaker = _result(
        "Keymaker",
        "unknown" if mfa is None else "no_flag" if mfa else "review",
        "Review account access and enable MFA where supported."
        if mfa is False else "Account security is not independently verified."
    )

    permission_counts = (
        f["location_permission_count"], f["microphone_permission_count"],
        f["camera_permission_count"],
    )
    seraph_status = (
        "unknown" if all(v is None for v in permission_counts)
        else "review" if any(v is not None and v > 0 for v in permission_counts)
        else "no_flag"
    )
    seraph = _result(
        "Seraph", seraph_status,
        "Review sensitive permissions individually; their existence is not proof of tracking."
    )

    updates = f["security_updates_current"]
    oracle = _result(
        "Oracle",
        "unknown" if updates is None else "no_flag" if updates else "review",
        "Review available security updates; no future threat is predicted."
    )

    specialist_results = (neo, morpheus, oracle, architect, keymaker, seraph)
    trinity_status = (
        "review" if any(r["status"] == "review" for r in specialist_results)
        else "unknown" if any(r["status"] == "unknown" for r in specialist_results)
        else "no_flag"
    )
    trinity = _result(
        "Trinity", trinity_status,
        "Coordinate a manual privacy review; no live workers were dispatched."
    )
    indexed = {r["agent"]: r for r in (*specialist_results, trinity)}
    workers = tuple(indexed[name] for name in _ROLES)
    return {
        "name": "SMI Matrix bounded privacy review",
        "mode": "offline_deterministic_advisory",
        "workers": workers,
        "status": trinity_status,
        "input_source": "founder_supplied_not_device_verified",
        "input_fields_observed": observed,
        "actual_device_scan": False,
        "independent_agent_execution_proven": False,
        "agent_runtime_connected": False,
        "external_action_taken": False,
        "permission_changes_made": False,
        "execution_granted": False,
        "guardian_hrm_verification": "required_for_consequential_action",
        "green_gate_passed": False,
        "founder_final_required": True,
        "no_flag_is_not_security_certification": True,
    }
