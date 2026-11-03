"""Bounded integration tests: no fabricated HRM proof or execution grant."""

import pytest

from mission_control.smi_kernel_audit_readback import KernelAuditReadback
from oap.smi import oap_mind_kernel


def test_missing_audit_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        oap_mind_kernel,
        "readback_kernel_audit",
        lambda **kwargs: KernelAuditReadback(
            kwargs["request_id"], False, False, "MISSING_OR_AMBIGUOUS_AUDIT"
        ),
    )
    result = oap_mind_kernel.assess_kernel_evidence(
        identity_id="founder", request_id="request"
    )
    assert result.octopus_assessment == "INVESTIGATE"
    assert not result.audit_verified
    assert not result.durable_hrm_receipt_proven
    assert not result.production_certified
    assert result.founder_final and result.advisory_only


def test_verified_audit_still_requires_hrm_receipt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        oap_mind_kernel,
        "readback_kernel_audit",
        lambda **kwargs: KernelAuditReadback(
            kwargs["request_id"], True, True, "CANONICAL_AUDIT_ROW_READ_BACK",
            "event-1",
        ),
    )
    result = oap_mind_kernel.assess_kernel_evidence(
        identity_id="founder", request_id="request"
    )
    assert result.audit_verified and result.execution_observed
    assert result.octopus_assessment == "INVESTIGATE"
    assert result.confidence == "AUDIT_ROW_ONLY_NOT_HRM_PROOF"
    assert result.next_evidence == "AUTHENTICATED_SUBJECT_BOUND_HRM_RECEIPT_REQUIRED"
    assert not result.durable_hrm_receipt_proven
    assert not result.production_certified


def test_canonical_blocked_execution_is_not_green(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        oap_mind_kernel,
        "readback_kernel_audit",
        lambda **kwargs: KernelAuditReadback(
            kwargs["request_id"], True, False, "CANONICAL_AUDIT_ROW_READ_BACK",
            "event-2",
        ),
    )
    result = oap_mind_kernel.assess_kernel_evidence(
        identity_id="founder", request_id="request"
    )
    assert result.octopus_assessment == "HOLD"
    assert not result.execution_observed
    assert not result.durable_hrm_receipt_proven


def test_founder_permission_denial_propagates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def deny(**kwargs: str) -> KernelAuditReadback:
        raise PermissionError("Founder authority required")

    monkeypatch.setattr(oap_mind_kernel, "readback_kernel_audit", deny)
    with pytest.raises(PermissionError):
        oap_mind_kernel.assess_kernel_evidence(
            identity_id="not-founder", request_id="request"
        )


def test_cross_request_audit_readback_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        oap_mind_kernel,
        "readback_kernel_audit",
        lambda **kwargs: KernelAuditReadback(
            "different-request", True, True, "CANONICAL_AUDIT_ROW_READ_BACK",
            "event-other",
        ),
    )
    result = oap_mind_kernel.assess_kernel_evidence(
        identity_id="founder", request_id="requested-id"
    )
    assert result.request_id == "requested-id"
    assert result.octopus_assessment == "HOLD"
    assert not result.audit_verified
    assert not result.execution_observed
    assert result.audit_event_id is None
    assert result.next_evidence == "AUDIT_REQUEST_BINDING_MISMATCH"
    assert not result.durable_hrm_receipt_proven


def test_missing_event_id_cannot_prove_canonical_audit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        oap_mind_kernel,
        "readback_kernel_audit",
        lambda **kwargs: KernelAuditReadback(
            kwargs["request_id"], True, True,
            "CANONICAL_AUDIT_ROW_READ_BACK", None,
        ),
    )
    result = oap_mind_kernel.assess_kernel_evidence(
        identity_id="founder", request_id="requested-id"
    )
    assert result.octopus_assessment == "HOLD"
    assert not result.audit_verified
    assert not result.execution_observed
    assert result.next_evidence == "AUDIT_EVENT_ID_REQUIRED"
