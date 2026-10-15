"""Read-only Matrix Command Room monitor projection.

No side effects, synthetic telemetry, permission changes or execution.
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from . import a6_matrix_execution, matrix_signal_bus


def neo_code_vision(observations: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Read-only Neo diagnostic projection; never invents runtime observations.

    Observations must be supplied by an authorised, evidence-bearing collector.
    This function does not collect telemetry, execute recovery or approve actions.
    """
    topology = matrix_signal_bus.topology()
    neo = next(
        (item for item in topology["participants"] if item["name"] == "Neo"),
        None,
    )
    registered = bool(neo and neo["status"] == "registered")
    findings: list[dict[str, str]] = []
    if observations is not None:
        if not isinstance(observations, Mapping):
            raise TypeError("observations must be a mapping")
        for service, observation in observations.items():
            if not isinstance(service, str) or not service.strip():
                raise ValueError("service names must be nonempty strings")
            if not isinstance(observation, Mapping):
                raise TypeError("each service observation must be a mapping")
            state = observation.get("state")
            evidence = observation.get("evidence")
            if state not in ("healthy", "degraded", "failed", "unknown"):
                raise ValueError("observation state must be healthy/degraded/failed/unknown")
            if not isinstance(evidence, str) or not evidence.strip():
                raise ValueError("each observation requires an evidence reference")
            findings.append({
                "service": service,
                "state": state,
                "evidence": evidence,
                "anomaly": "confirmed" if state in ("degraded", "failed") else "not_confirmed",
            })
    anomalies = [item for item in findings if item["anomaly"] == "confirmed"]
    return {
        "character": "Neo",
        "role": "kernel_sentinel_true_path_recovery",
        "registered": registered,
        "mode": "read_only",
        "code_vision": {
            "state": "evidence_supplied" if findings else "not_connected",
            "observations": tuple(findings),
            "source": "caller_supplied_evidence" if findings else None,
        },
        "anomaly_intelligence": {
            "confirmed_count": len(anomalies),
            "findings": tuple(anomalies),
            "all_clear_proven": bool(findings) and not anomalies and all(
                item["state"] == "healthy" for item in findings
            ),
        },
        "true_path_recovery": {
            "state": "requires_authorised_diagnosis" if anomalies else "not_assessed",
            "recommended_action": "investigate_evidence" if anomalies else None,
            "execution_granted": False,
            "guardian_required": True,
            "human_authority_final": True,
            "recovery_verified": False,
        },
        "full_green": False,
    }


def monitor_snapshot() -> dict[str, Any]:
    """Return explicitly sourced monitor data for existing War Room UI."""
    topology = matrix_signal_bus.topology()
    a6 = a6_matrix_execution.status()
    return {
        "name": "Matrix Command Room",
        "mode": "read_only",
        "parent": "SMI War Room",
        "agent_monitor": {
            "source": "matrix_signal_bus.topology",
            "registered": topology["registered_count"],
            "passport_review": topology["extended_review_count"],
            "participants": topology["participants"],
            "execution_granted": topology["execution_granted"],
        },
        "execution_monitor": {
            "source": "a6_matrix_execution.status",
            "enabled": a6["enabled"],
            "a6_readiness_proven": a6["a6_readiness_proven"],
            "operation_level_approval_required": a6["operation_level_approval_required"],
            "guardian_required": a6["guardian_required"],
            "rollback_required": a6["rollback_required"],
        },
        "telemetry_monitor": {
            "state": "not_connected",
            "cpu": None,
            "memory": None,
            "latency_ms": None,
            "availability": None,
        },
        "test_monitor": {"state": "not_connected", "last_run": None, "passed": None},
        "controls": {
            "inspect": "read_only",
            "run_tests": "not_connected",
            "recover": "not_connected",
            "approve": "not_available_in_this_projection",
        },
        "neo_monitor": neo_code_vision(),
        "full_green": False,
        "founder_final": True,
    }
