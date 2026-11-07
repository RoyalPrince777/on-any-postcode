"""Read-only OAP MIND assessment of the existing canonical Living Kernel audit.

This is an integration with the OAP audit readback, not a replacement HRM
receipt validator, an execution action, or an independent intelligence brain.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

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
    hrm_signal_receipt_observed: bool = False
    hrm_signal_binding: str = "NOT_ESTABLISHED"


def assess_kernel_evidence(\n    *, identity_id: str, request_id: str, hrm_signal_id: str | None = None\n) -> KernelMindReview:
    """Require authoritative Founder-bound audit readback, never caller flags.

    The canonical readback enforces a human authority check. Its PermissionError
    deliberately propagates; missing or inconsistent audit rows fail closed.
    """
    audit = readback_kernel_audit(identity_id=identity_id, request_id=request_id)
    # Defend the OAP MIND boundary against cross-request or incomplete readbacks.
    # The canonical readback remains responsible for human-authority validation.
    if audit.request_id != request_id:
        return KernelMindReview(
            request_id=request_id,
            audit_event_id=None,
            octopus_assessment="HOLD",
            audit_verified=False,
            execution_observed=False,
            durable_hrm_receipt_proven=False,
            confidence="PROVENANCE_MISMATCH",
            next_evidence="AUDIT_REQUEST_BINDING_MISMATCH",
        )
    if audit.verified and not audit.event_id:
        return KernelMindReview(
            request_id=request_id,
            audit_event_id=None,
            octopus_assessment="HOLD",
            audit_verified=False,
            execution_observed=False,
            durable_hrm_receipt_proven=False,
            confidence="INSUFFICIENT",
            next_evidence="AUDIT_EVENT_ID_REQUIRED",
        )
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

    # Signal-scoped readback is diagnostic ONLY: it cannot authenticate the
    # relationship between this audit's request ID and an HRM signal.
    if not audit.executed or hrm_signal_id is None:
        return review
    if not isinstance(hrm_signal_id, str) or not hrm_signal_id.strip():
        return replace(review, hrm_signal_binding="INVALID_SIGNAL_ID")

    from mission_control.hrm_durable_receipt import latest_receipt_status

    try:
        status = latest_receipt_status(hrm_signal_id.strip())
    except Exception:  # noqa: BLE001 - diagnostics never bypass Green Gate
        return replace(review, hrm_signal_binding="SIGNAL_STATUS_UNAVAILABLE")
    if not isinstance(status, dict):
        return replace(review, hrm_signal_binding="SIGNAL_STATUS_UNAVAILABLE")
    if status.get("read_back_verified") is True and status.get("found") is True:
        return replace(
            review,
            hrm_signal_receipt_observed=True,
            hrm_signal_binding="SIGNAL_RECEIPT_VALID_BUT_REQUEST_UNBOUND",
        )
    return replace(review, hrm_signal_binding="SIGNAL_RECEIPT_UNVERIFIED_OR_MISSING")
