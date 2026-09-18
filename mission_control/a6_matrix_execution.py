"""Matrix-governed A6 operation gate.

A6 may be enabled as a capability, but every operation remains fail-closed until
the production readiness gate, Matrix control plane, Founder approval, Guardian,
Green Gate, rollback, and receipt-chain conditions all pass. The only live
operation orchestrated here is the allowlisted read-only Route Matrix capture;
it cannot expand authority or mutate product state.
"""
from __future__ import annotations

from typing import Any

from . import (
    a7_certification,
    autonomy_levels,
    maps_movement_direct_proof_runner,
    matrix_signal_bus,
)


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



def run_route_matrix_lane(
    *,
    identity_id: object,
    base_url: object,
    operation_id: object,
    founder_approved: bool,
    guardian_pass: bool,
    green_gate_pass: bool,
    rollback_proven: bool,
    receipt_chain_ready: bool,
) -> dict[str, Any]:
    """Run the bounded Route Matrix in its canonical A6 governed position."""

    gate = precheck(
        "ROUTE_MATRIX_CAPTURE",
        founder_approved=founder_approved,
        guardian_pass=guardian_pass,
        green_gate_pass=green_gate_pass,
        rollback_proven=rollback_proven,
        receipt_chain_ready=receipt_chain_ready,
    )
    if not gate.get("allowed"):
        runtime = gate.get("runtime") if isinstance(gate.get("runtime"), dict) else {}
        raise RuntimeError(
            "a6_route_matrix_precheck_blocked:"
            + str(gate.get("reason") or "unknown")[:60]
            + f":level={runtime.get('configured_level')}"
            + f":readiness={bool(runtime.get('a6_readiness_proven'))}"
            + f":matrix={bool(runtime.get('matrix_ready'))}"
            + f":matrix_count={runtime.get('matrix_registered_count')}"
            + f":enabled={bool(runtime.get('enabled'))}"
        )

    capture = maps_movement_direct_proof_runner.execute_route_matrix_capture(
        identity_id=identity_id,
        base_url=base_url,
        operation_id=operation_id,
    )
    receipt_verified = bool(
        capture.get("receipt_write_verified")
        and capture.get("receipt_read_back_verified")
    )
    matrix_postcheck = postcheck(
        "ROUTE_MATRIX_CAPTURE",
        operation_succeeded=bool(capture.get("passed")),
        rollback_still_available=True,
        receipt_recorded=receipt_verified,
    )
    success = bool(capture.get("passed") and matrix_postcheck.get("passed"))
    return {
        "component": "A6 Route Matrix Governed Lane",
        "position": "SMI/A6 Governed Execution/Route Matrix/Live Capture",
        "sequence": (
            "Founder Approval",
            "Guardian",
            "Green Gate",
            "A6 Matrix Precheck",
            "Route Matrix Live Capture",
            "7-7-7 HRM Receipt",
            "Matrix Postcheck",
            "Safe Diagnostic",
            "JOOG/HRM Record",
        ),
        "success": success,
        "public_probe_pass": bool(capture.get("public_probe_pass")),
        "private_fail_closed_pass": bool(capture.get("private_fail_closed_pass")),
        "receipt_verified": receipt_verified,
        "matrix_postcheck_pass": bool(matrix_postcheck.get("passed")),
        "production_state_mutated": False,
        "authority_expanded": False,
        "human_authority_final": True,
        "capture": capture,
        "postcheck": matrix_postcheck,
    }
