"""Trusted audit-to-HRM bridge never mints durable proof from an unverified audit."""

from unittest.mock import patch

from mission_control.smi_kernel_audit_readback import KernelAuditReadback
from mission_control.smi_kernel_hrm_evidence import record_verified_kernel_evidence


def test_missing_audit_never_writes_hrm():
    with (
        patch(
            "mission_control.smi_kernel_hrm_evidence.readback_kernel_audit",
            return_value=KernelAuditReadback("req", False, False, "MISSING"),
        ),
        patch("mission_control.smi_kernel_hrm_evidence.write_receipt") as write,
    ):
        result = record_verified_kernel_evidence(identity_id="founder", request_id="req")
    assert not result.hrm_durable
    write.assert_not_called()


def test_blocked_audit_never_writes_hrm():
    with (
        patch(
            "mission_control.smi_kernel_hrm_evidence.readback_kernel_audit",
            return_value=KernelAuditReadback("req", True, False, "BLOCKED", "event"),
        ),
        patch("mission_control.smi_kernel_hrm_evidence.write_receipt") as write,
    ):
        result = record_verified_kernel_evidence(identity_id="founder", request_id="req")
    assert not result.execution_verified
    write.assert_not_called()


def test_durable_hrm_requires_independent_readback():
    with (
        patch(
            "mission_control.smi_kernel_hrm_evidence.readback_kernel_audit",
            return_value=KernelAuditReadback("req", True, True, "VERIFIED", "event"),
        ),
        patch(
            "mission_control.smi_kernel_hrm_evidence.write_receipt",
            return_value={"ok": True, "read_back_ok": True, "durable": True,
                          "fallback_used": False, "backend": "independent_hrm_postgres",
                          "receipt_id": "hrm-id"},
        ) as write,
    ):
        result = record_verified_kernel_evidence(identity_id="founder", request_id="req")
    assert result.hrm_durable and result.hrm_receipt_id == "hrm-id"
    assert write.call_args.kwargs["require_durable"] is True
    assert write.call_args.args[1]["safe_payload"]["canonical_audit_event_id"] == "event"


def test_sqlite_fallback_never_proves_durability():
    with (
        patch(
            "mission_control.smi_kernel_hrm_evidence.readback_kernel_audit",
            return_value=KernelAuditReadback("req", True, True, "VERIFIED", "event"),
        ),
        patch(
            "mission_control.smi_kernel_hrm_evidence.write_receipt",
            return_value={"ok": True, "read_back_ok": True, "durable": False,
                          "fallback_used": True, "backend": "local_sqlite_receipt_store"},
        ),
    ):
        result = record_verified_kernel_evidence(identity_id="founder", request_id="req")
    assert result.audit_verified and result.execution_verified
    assert not result.hrm_durable
    assert result.hrm_receipt_id is None
