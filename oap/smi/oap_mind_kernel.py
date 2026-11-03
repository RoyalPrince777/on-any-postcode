"""Read-only OAP MIND assessment of the existing canonical Living Kernel audit.

This is an integration with the OAP audit readback, not a replacement HRM
receipt validator, an execution action, or an independent intelligence brain.
"""

from __future__ import annotations

from dataclasses import dataclass

from mission_control.smi_kernel_audit_readback import readback_kernel_audit


@dataclass(frozen=True)
class KernelMindReview:
    request_id: str
    audit_event_id: str | None
    octopus_assessment: str
    audit_verified: bool
    execution_observed: bool
    durable_hrm_receipt_proven: bool
    confidence: str
    next_evidence: str
    specialist: str = "Octopus"
    capability: str = "OAP Metacognitive Intelligence"
    advisory_only: bool = True
    founder_final: bool = True
    production_certified: bool = False


def assess_kernel_evidence(*, identity_id: str, request_id: str) -> KernelMindReview:
    """Require authoritative Founder-bound audit readback, never caller flags.

    The canonical readback enforces a human authority check. Its PermissionError
    deliberately propagates; missing or inconsistent audit rows fail closed.
    """
    audit = readback_kernel_audit(identity_id=identity_id, request_id=request_id)
    if not audit.verified:
        return KernelMindReview(
            request_id=audit.request_id,
            audit_event_id=None,
            octopus_assessment="INVESTIGATE",
            audit_verified=False,
            execution_observed=False,
            durable_hrm_receipt_proven=False,
            confidence="INSUFFICIENT",
            next_evidence=audit.reason,
        )
    return KernelMindReview(
        request_id=audit.request_id,
        audit_event_id=audit.event_id,
        octopus_assessment="INVESTIGATE" if audit.executed else "HOLD",
        audit_verified=True,
        execution_observed=audit.executed,
        durable_hrm_receipt_proven=False,
        confidence="AUDIT_ROW_ONLY_NOT_HRM_PROOF",
        next_evidence=(
            "AUTHENTICATED_SUBJECT_BOUND_HRM_RECEIPT_REQUIRED"
            if audit.executed else "EXECUTION_BLOCKED"
        ),
    )
