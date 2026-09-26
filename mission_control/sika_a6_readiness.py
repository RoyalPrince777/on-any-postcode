"""SIKA A6 readiness adapter.

Reuses the canonical A6 Matrix gate. It exposes readiness only and never grants
execution, money movement, permission expansion, or A7 authority.
"""
from __future__ import annotations

from typing import Any

from . import a6_matrix_execution, a7_certification, autonomy_levels


def status() -> dict[str, Any]:
    autonomy = autonomy_levels.status()
    proof = a7_certification.status()
    matrix = a6_matrix_execution.status()
    missing = list(proof.get("a6_missing") or ())
    return {
        "level": "A6",
        "name": autonomy_levels.AUTONOMY_LEVELS["A6"],
        "configured_level": autonomy.get("configured_level"),
        "a6_capability_enabled": bool(autonomy.get("a6_enabled")),
        "matrix_control_enabled": bool(autonomy.get("a6_matrix_control")),
        "matrix_ready": bool(matrix.get("matrix_ready")),
        "a6_readiness_proven": bool(matrix.get("a6_readiness_proven")),
        "missing_proofs": missing,
        "operation_level_approval_required": True,
        "guardian_required": True,
        "green_gate_required": True,
        "rollback_required": True,
        "hrm_receipt_required": True,
        "matrix_precheck_required": True,
        "matrix_postcheck_required": True,
        "payment_or_value_transfer_forbidden_without_regulated_authority": True,
        "execution_granted": False,
        "payment_execution_enabled": False,
        "a7_enabled": False,
        "self_permission_change_allowed": False,
        "human_authority_final": True,
    }
