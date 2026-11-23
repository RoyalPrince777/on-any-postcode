"""Six bounded Matrix privacy intelligence reviews over existing SMI components.

This module is a pure, offline advisory projection. It accepts only coarse
Founder-supplied booleans/counts; it neither reads Android data nor starts jobs.
Do not turn a self-report into proof of surveillance or of device security.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from . import autonomy_levels, matrix_privacy_workers

_DOMAIN_FIELDS: dict[str, dict[str, str]] = {
    "identity_shield": {
        "unrecognised_signin_alert": "risk_bool",
        "unexpected_recovery_alert": "risk_bool",
        "account_mfa_enabled": "protective_bool",
    },
    "network_intelligence": {
        "unexpected_network_change": "risk_bool",
        "unrecognised_network_count": "risk_count",
        "private_dns_configured": "information_bool",
    },
    "offline_recovery": {
        "offline_guide_available": "protective_bool",
        "recovery_walkthrough_tested": "protective_bool",
    },
}

_PRIORITIES: tuple[str, ...] = (
    "on_device_privacy_intelligence",
    "identity_shield",
    "network_intelligence",
    "offline_recovery",
    "evidence_intelligence",
    "governed_worker_automation",
)
_PRIVACY_JOB_TYPE = "MATRIX_PRIVACY_REVIEW"


def _validate_facts(
    domain: str, facts: Mapping[str, object] | None,
) -> dict[str, bool | int | None]:
    if facts is None:
        facts = {}
    if not isinstance(facts, Mapping):
        raise TypeError("Domain facts must be a mapping")
    if any(type(key) is not str for key in facts):
        raise ValueError("Only named fact fields are accepted")
    schema = _DOMAIN_FIELDS[domain]
    if set(facts) - set(schema):
        raise ValueError("Unsupported or potentially sensitive fact field")
    normalised: dict[str, bool | int | None] = {}
    for name, kind in schema.items():
        value = facts.get(name)
        if value is not None:
            if kind == "risk_count":
                if type(value) is not int or not 0 <= value <= 1000:
                    raise ValueError("Counts must be bounded non-negative integers")
            elif type(value) is not bool:
                raise ValueError("Indicators must be booleans")
        normalised[name] = value
    return normalised


def _risk_status(domain: str, facts: Mapping[str, bool | int | None]) -> str:
    schema = _DOMAIN_FIELDS[domain]
    has_risk = any(
        (kind == "risk_bool" and facts[name] is True)
        or (kind == "risk_count" and facts[name] is not None and facts[name] > 0)
        or (kind == "protective_bool" and facts[name] is False)
        for name, kind in schema.items()
    )
    if has_risk:
        return "review"
    if any(value is None for value in facts.values()):
        return "unknown"
    return "no_flag"


def _summary(
    domain: str, facts: Mapping[str, bool | int | None],
    *, owner: str, next_step: str,
) -> dict[str, Any]:
    return {
        "priority": domain,
        "owner": owner,
        "status": _risk_status(domain, facts),
        "input_fields_observed": sum(value is not None for value in facts.values()),
        "input_provenance": "founder_supplied_unverified",
        "independent_evidence_verified": False,
        "next_step": next_step,
        "executed": False,
    }


def review_matrix_privacy_priorities(
    *,
    device_facts: Mapping[str, object] | None = None,
    identity_facts: Mapping[str, object] | None = None,
    network_facts: Mapping[str, object] | None = None,
    recovery_facts: Mapping[str, object] | None = None,
) -> dict[str, Any]:
    """Prepare six domain reviews and a non-dispatching worker preflight.

    No raw identity, location, account, packet, tracker, network, biometric,
    recovery-code, or session data may enter this allowlisted interface.
    """
    device = matrix_privacy_workers.review_founder_device_facts(
        {} if device_facts is None else device_facts
    )
    identity = _validate_facts("identity_shield", identity_facts)
    network = _validate_facts("network_intelligence", network_facts)
    recovery = _validate_facts("offline_recovery", recovery_facts)

    # Use canonical runtime policy rather than adding a new job allowance.
    # This is only a read-only policy evaluation; no job is enqueued.
    policy = autonomy_levels.evaluate_runtime_job(_PRIVACY_JOB_TYPE)

    domains: tuple[dict[str, Any], ...] = (
        {
            "priority": _PRIORITIES[0],
            "owner": "Neo",
            "status": device["status"],
            "input_fields_observed": device["input_fields_observed"],
            "input_provenance": "founder_supplied_unverified",
            "independent_evidence_verified": False,
            "next_step": "Review built-in tracker alerts and permissions manually.",
            "executed": False,
        },
        _summary(
            "identity_shield", identity, owner="Keymaker",
            next_step="Verify account alerts using the provider's own authenticated security screen; no credentials or session tokens.",
        ),
        _summary(
            "network_intelligence", network, owner="Architect",
            next_step="Inspect the Android network settings manually; no packet capture or network probing.",
        ),
        _summary(
            "offline_recovery", recovery, owner="Trinity",
            next_step="Review a local recovery guide without storing credentials, account records, HRM decisions or approvals in offline caches.",
        ),
        {
            "priority": "evidence_intelligence",
            "owner": "Morpheus",
            "status": "unknown",
            "input_provenance": "founder_supplied_unverified",
            "independent_evidence_verified": False,
            "durable_hrm_receipt_proven": False,
            "surveillance_confirmed": False,
            "next_step": "Require independent trusted readback before marking a finding verified.",
            "executed": False,
        },
        {
            "priority": "governed_worker_automation",
            "owner": "Seraph",
            "status": "unknown",
            "proposed_job_type": _PRIVACY_JOB_TYPE,
            "policy_allowed": policy["allowed"] is True,
            "policy_reason": str(policy["reason"]),
            "preflight_only": True,
            "dispatch_authorised": False,
            "job_enqueued": False,
            "worker_launched": False,
            "next_step": "Separate security-reviewed adapter, runtime allowlist change, guarded approval and exact-head tests required.",
            "executed": False,
        },
    )

    return {
        "name": "SMI Matrix Privacy Intelligence Six-Priority Review",
        "mode": "offline_advisory_no_telemetry",
        "priorities": domains,
        "priority_count": len(domains),
        "matrix_agents": tuple(worker["agent"] for worker in device["workers"]),
        "matrix_role_count": len(device["workers"]),
        "overall_status": (
            "review" if any(item["status"] == "review" for item in domains)
            else "unknown"
        ),
        "data_source": "founder_supplied_facts_only",
        "biometric_templates_collected": False,
        "gps_history_collected": False,
        "raw_network_traffic_collected": False,
        "credentials_collected": False,
        "data_persisted": False,
        "network_calls_made": False,
        "live_device_access": False,
        "automatic_blocking": False,
        "independent_agent_execution_proven": False,
        "runtime_dispatch_authorised": False,
        "permissions_expanded": False,
        "outside_provider_added": False,
        "guardian_hrm_independent_verification": False,
        "war_room_review_required": True,
        "green_gate_passed": False,
        "founder_final_required_for_execution": True,
        "deployment_authorised": False,
        "security_certified": False,
    }
