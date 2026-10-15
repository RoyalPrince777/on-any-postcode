"""Read-only Matrix Command Room monitor projection.

No side effects, synthetic telemetry, permission changes or execution.
"""
from __future__ import annotations

from typing import Any

from . import a6_matrix_execution, matrix_signal_bus


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
        "full_green": False,
        "founder_final": True,
    }
