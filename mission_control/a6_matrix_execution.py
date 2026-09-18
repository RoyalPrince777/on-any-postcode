"""Matrix-governed A6 operation gate.

A6 may be enabled as a capability, but every operation remains fail-closed until
the production readiness gate, Matrix control plane, Founder approval, Guardian,
Green Gate, rollback, and receipt-chain conditions all pass. This module does
not itself execute external side effects.
"""
from __future__ import annotations

from typing import Any

from . import a7_certification, autonomy_levels, matrix_signal_bus


def status() -> dict[str, Any]:
    autonomy = autonomy_levels.status()
    proof = a7_certification.status()
    matrix = matrix_signal_bus.topology()
    matrix_ready = bool(
        matrix.get("registered_count") == len(matrix_signal_bus.CORE_MATRIX_ORDER)
        and matrix.get("final_authority") == "Human Authority"
        and matrix.get("protector") == "Guardian"
        and matrix.get("proof_gate") == "Green Gate"
    )
    enabled = bool(
        autonomy.get("a6_enabled")
        and autonomy.get("a6_matrix_control")
        and proof.get("a6_proof_complete")
        and matrix_ready
    )
    return {
        "component": "A6 Matrix Governed Execution",
        "enabled": enabled,
        "configured_level": autonomy.get("configured_level"),
        "a6_readiness_proven": bool(proof.get("a6_proof_complete")),
        "matrix_ready": matrix_ready,
        "matrix_registered_count": matrix.get("registered_count"),
        "allowlisted_actions": autonomy.get("a6_execution_actions", ()),
        "operation_level_approval_required": True,
        "guardian_required": True,
        "green_gate_required": True,
        "rollback_required": True,
        "hrm_receipt_required": True,
        "matrix_precheck_required": True,
        "matrix_postcheck_required": True,
        "forbidden_domains": autonomy.get("forbidden_domains", ()),
        "authority_expansion_allowed": False,
        "human_authority_final": True,
    }


def precheck(
    action_type: object,
    *,
    founder_approved: bool,
    guardian_pass: bool,
    green_gate_pass: bool,
    rollback_proven: bool,
    receipt_chain_ready: bool,
) -> dict[str, Any]:
    runtime = status()
    action = str(action_type or "").strip().upper()
    signal = matrix_signal_bus.route_signal(
        sender="Neo",
        topic=f"A6 precheck: {action or 'UNKNOWN'}",
        kind="governance_precheck",
        recipients=(
            "Trinity",
            "SMI",
            "Guardian",
            "Green Gate",
            "War Room",
            "Human Authority",
        ),
        urgency="high",
        requested_action="review_before_execution",
        consequential=True,
    )
    decision = autonomy_levels.evaluate_a6_operation(
        action,
        founder_approved=founder_approved,
        guardian_pass=guardian_pass,
        green_gate_pass=green_gate_pass,
        rollback_proven=rollback_proven,
        receipt_chain_ready=receipt_chain_ready,
        matrix_precheck_pass=bool(runtime["enabled"]),
    )
    allowed = bool(runtime["enabled"] and decision["allowed"])
    return {
        "allowed": allowed,
        "action_type": action,
        "reason": decision["reason"] if runtime["enabled"] else "a6_readiness_or_matrix_not_ready",
        "runtime": runtime,
        "decision": decision,
        "matrix_signal": signal,
        "execution_granted": allowed,
        "postcheck_required": allowed,
        "human_authority_final": True,
    }


def postcheck(
    action_type: object,
    *,
    operation_succeeded: bool,
    rollback_still_available: bool,
    receipt_recorded: bool,
) -> dict[str, Any]:
    action = str(action_type or "").strip().upper()
    passed = bool(
        operation_succeeded is True
        and rollback_still_available is True
        and receipt_recorded is True
    )
    signal = matrix_signal_bus.route_signal(
        sender="Neo",
        topic=f"A6 postcheck: {action or 'UNKNOWN'}",
        kind="governance_postcheck",
        recipients=("Trinity", "SMI", "Guardian", "Green Gate", "War Room"),
        urgency="high" if not passed else "normal",
        requested_action="verify_or_rollback",
        consequential=True,
    )
    return {
        "passed": passed,
        "action_type": action,
        "rollback_required": not passed,
        "halt_further_execution": not passed,
        "matrix_signal": signal,
        "human_authority_final": True,
    }
