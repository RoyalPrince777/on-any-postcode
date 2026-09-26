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


def fail_closed_precheck(action_type: object = "ROUTE_MATRIX_CAPTURE") -> dict[str, Any]:
    """Exercise the canonical A6 precheck with every consequential control false.

    This is real policy execution against the current software state, not a grant
    of A6 authority and not a production side effect.
    """
    result = a6_matrix_execution.precheck(
        action_type,
        founder_approved=False,
        guardian_pass=False,
        green_gate_pass=False,
        rollback_proven=False,
        receipt_chain_ready=False,
    )
    return {
        "action_type": result.get("action_type"),
        "allowed": bool(result.get("allowed")),
        "reason": result.get("reason"),
        "execution_granted": bool(result.get("execution_granted")),
        "postcheck_required": bool(result.get("postcheck_required")),
        "human_authority_final": bool(result.get("human_authority_final")),
        "proof_class": "software_policy_execution",
    }


def evidence_pack() -> dict[str, Any]:
    current = status()
    return {
        "level": "A6",
        "missing_proofs": current["missing_proofs"],
        "required_external_or_durable_evidence": {
            "independent_proof_runner": True,
            "operation_level_human_approval": True,
            "guardian_pass": True,
            "green_gate": True,
            "operation_specific_rollback": True,
            "consequential_action_receipt_chain": True,
            "hrm_receipts": True,
        },
        "software_fail_closed_precheck": fail_closed_precheck(),
        "execution_granted": False,
        "production_state_mutated": False,
        "payment_execution_enabled": False,
        "human_authority_final": True,
    }
