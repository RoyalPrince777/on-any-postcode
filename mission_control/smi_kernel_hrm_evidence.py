"""Founder-gated canonical audit -> independently read-back HRM evidence.

Uses existing audit reader and HRM receipt backend; never executes an action.
"""

from __future__ import annotations

from dataclasses import dataclass

from .smi_kernel_audit_readback import readback_kernel_audit
from .smi_receipt_backend import write_receipt


@dataclass(frozen=True)
class DurableKernelEvidence:
    request_id: str
    audit_verified: bool
    execution_verified: bool
    hrm_durable: bool
    reason: str
    hrm_receipt_id: str | None = None


def record_verified_kernel_evidence(
    *, identity_id: str, request_id: str,
) -> DurableKernelEvidence:
    """Persist bounded evidence only after canonical Founder-gated audit readback."""
    audit = readback_kernel_audit(identity_id=identity_id, request_id=request_id)
    if not audit.verified or not audit.executed or not audit.event_id:
        return DurableKernelEvidence(
            audit.request_id, audit.verified, False, False,
            "CANONICAL_AUDIT_NOT_EXECUTED_OR_UNVERIFIED",
        )
    proof = write_receipt(
        "hrm_neon_evidence_receipt",
        {
            "brain_part": "founder_kernel_audit",
            "gate": 75,
            "command": "kernel_audit_readback",
            "signal": "🟣",
            "guardian": "required",
            "green_gate": "pending_full_verification",
            "founder_final": "required",
            "safe_payload": {
                "request_id": audit.request_id,
                "canonical_audit_event_id": audit.event_id,
                "canonical_audit_readback": True,
                "kernel_execution_recorded": True,
                "external_action_executed_by_this_bridge": False,
            },
        },
        require_durable=True,
    )
    durable = bool(
        proof.get("ok") is True
        and proof.get("read_back_ok") is True
        and proof.get("durable") is True
        and proof.get("fallback_used") is False
        and proof.get("backend") == "independent_hrm_postgres"
    )
    return DurableKernelEvidence(
        audit.request_id, True, True, durable,
        "DURABLE_HRM_RECEIPT_READ_BACK" if durable else "HRM_DURABILITY_UNPROVEN",
        str(proof.get("receipt_id")) if durable else None,
    )
