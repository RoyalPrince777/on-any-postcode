"""Execution evidence must never imply an unverified durable receipt."""

from oap.smi.execution_evidence import classify_kernel_outcome


def test_missing_provenance_fails_closed():
    result = classify_kernel_outcome({"request_id": "r", "executed": True})
    assert result.stage == "UNVERIFIED"
    assert not result.evidence_verified


def test_blocked_action_stays_blocked():
    result = classify_kernel_outcome({
        "request_id": "r", "living_kernel": True,
        "human_authority_final": True, "executed": False,
        "audit_event_id": "a",
    })
    assert result.stage == "BLOCKED"
    assert not result.durable_receipt_proven


def test_execution_without_audit_is_unverified():
    result = classify_kernel_outcome({
        "request_id": "r", "living_kernel": True,
        "human_authority_final": True, "executed": True,
    })
    assert result.reason == "MISSING_AUDIT_REFERENCE"


def test_audit_reference_is_not_durable_readback():
    result = classify_kernel_outcome({
        "request_id": "r", "living_kernel": True,
        "human_authority_final": True, "executed": True,
        "audit_event_id": "a",
    })
    assert result.executed
    assert result.audit_event_id == "a"
    assert result.stage == "EXECUTED_UNVERIFIED"
    assert not result.evidence_verified
    assert not result.durable_receipt_proven
