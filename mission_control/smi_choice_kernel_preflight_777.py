"""Read-only SMI choice-to-kernel preflight; no execution authority.

Only the existing LivingKernel.coordinate can process a valid approval receipt.
"""
from __future__ import annotations

from mission_control.smi_choice_protocol_777 import compare_choices, execution_gate


def preflight_choice(mission_id, choice, options, approvals=None):
    """Compare options and describe what must be proven before kernel handoff."""
    comparison = compare_choices(mission_id, choice, options)
    if not comparison.get("ready"):
        return {"ready": False, "reason": comparison["reason"], "executed": False}
    approvals = approvals if isinstance(approvals, dict) else {}
    return {
        "ready": True,
        "mission_id": mission_id,
        "choice": choice,
        "comparison": comparison["comparison"],
        "suggested_specialists": comparison["suggested_specialists"],
        "advisory_gates_satisfied": execution_gate(approvals),
        "kernel_receipt_verified": False,
        "guardian_runtime_verified": False,
        "hrm_receipt_recorded": False,
        "executed": False,
        "votes_executed": False,
        "operational_vpi": None,
        "next_authority": "existing LivingKernel human approval workflow",
    }
