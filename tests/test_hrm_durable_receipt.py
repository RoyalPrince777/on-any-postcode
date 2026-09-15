import pytest

from mission_control.hrm_durable_receipt import ReceiptBlocked, build_receipt, persist_and_read_back


def proof_payload(**overrides):
    payload = {
        "governance": "7-7-7",
        "checks": {
            "mind": {f"m{i}": True for i in range(7)},
            "body": {f"b{i}": True for i in range(7)},
            "soul": {f"s{i}": True for i in range(7)},
        },
        "evidence_proven": True,
        "authority_transferred": False,
        "human_authority_required": False,
        "human_authority_approved": False,
    }
    payload.update(overrides)
    return payload


def test_receipt_requires_exact_777():
    payload = proof_payload()
    payload["checks"]["mind"].pop("m6")
    with pytest.raises(ReceiptBlocked, match="mind_seven_checks_required"):
        build_receipt("sig-1", payload)


def test_receipt_requires_evidence():
    with pytest.raises(ReceiptBlocked, match="evidence_required"):
        build_receipt("sig-2", proof_payload(evidence_proven=False))


def test_receipt_forbids_authority_transfer():
    with pytest.raises(ReceiptBlocked, match="authority_escalation_forbidden"):
        build_receipt("sig-3", proof_payload(authority_transferred=True))


def test_human_authority_fails_closed_when_required():
    with pytest.raises(ReceiptBlocked, match="human_authority_required"):
        build_receipt("sig-4", proof_payload(human_authority_required=True))


def test_write_path_disabled_by_default(monkeypatch):
    monkeypatch.delenv("OAP_HRM_DURABLE_WRITES_ENABLED", raising=False)
    receipt = build_receipt("sig-5", proof_payload())
    with pytest.raises(ReceiptBlocked, match="durable_writes_disabled"):
        persist_and_read_back(receipt)


def test_receipt_id_is_stable_for_same_receipt_content(monkeypatch):
    import mission_control.hrm_durable_receipt as module
    class FixedDateTime:
        @classmethod
        def now(cls, tz):
            from datetime import datetime
            return datetime(2026, 9, 15, tzinfo=tz)
    monkeypatch.setattr(module, "datetime", FixedDateTime)
    first = build_receipt("sig-6", proof_payload())
    second = build_receipt("sig-6", proof_payload())
    assert first.receipt_id == second.receipt_id
    assert first.checksum == second.checksum
