import pytest

from mission_control.hrm_agent_lifecycle import BODY_7, MIND_7, SOUL_7
from mission_control.hrm_durable_receipt import (
    ReceiptBlocked,
    build_receipt,
    persist_and_read_back,
)


def proof_payload(**overrides):
    payload = {
        "governance": "7-7-7",
        "checks": {
            "mind": {name: True for name in MIND_7},
            "body": {name: True for name in BODY_7},
            "soul": {name: True for name in SOUL_7},
        },
        "evidence_proven": True,
        "authority_transferred": False,
        "human_authority_required": False,
        "human_authority_approved": False,
    }
    payload.update(overrides)
    return payload


def receipt(signal="sig-1", key="attempt-1", payload=None):
    return build_receipt(signal, payload or proof_payload(), idempotency_key=key)


def test_requires_canonical_check_names():
    payload = proof_payload()
    payload["checks"]["mind"] = {f"m{i}": True for i in range(7)}
    with pytest.raises(ReceiptBlocked, match="mind_canonical_checks_required"):
        receipt(payload=payload)


def test_requires_all_three_canonical_planes():
    payload = proof_payload()
    payload["checks"].pop("soul")
    with pytest.raises(ReceiptBlocked, match="canonical_governance_checks_required"):
        receipt(payload=payload)


def test_requires_evidence():
    with pytest.raises(ReceiptBlocked, match="evidence_required"):
        receipt(payload=proof_payload(evidence_proven=False))


def test_forbids_authority_transfer():
    with pytest.raises(ReceiptBlocked, match="authority_escalation_forbidden"):
        receipt(payload=proof_payload(authority_transferred=True))


def test_human_authority_fails_closed_when_required():
    with pytest.raises(ReceiptBlocked, match="human_authority_required"):
        receipt(payload=proof_payload(human_authority_required=True))


def test_requires_idempotency_key():
    with pytest.raises(ReceiptBlocked, match="idempotency_key_required"):
        build_receipt("sig", proof_payload(), idempotency_key="")


def test_requires_signal_id():
    with pytest.raises(ReceiptBlocked, match="signal_id_required"):
        build_receipt(" ", proof_payload(), idempotency_key="attempt")


def test_retry_identity_is_stable_despite_recorded_time(monkeypatch):
    import mission_control.hrm_durable_receipt as module

    class MovingDateTime:
        calls = 0

        @classmethod
        def now(cls, tz):
            from datetime import datetime

            cls.calls += 1
            return datetime(2026, 9, 15, 12, 0, cls.calls, tzinfo=tz)

    monkeypatch.setattr(module, "datetime", MovingDateTime)
    first = receipt("sig-retry", "same-attempt")
    second = receipt("sig-retry", "same-attempt")
    assert first.receipt_id == second.receipt_id
    assert first.checksum == second.checksum
    assert first.payload["recorded_at"] != second.payload["recorded_at"]


def test_write_path_disabled_by_default(monkeypatch):
    monkeypatch.delenv("OAP_HRM_DURABLE_WRITES_ENABLED", raising=False)
    with pytest.raises(ReceiptBlocked, match="durable_writes_disabled"):
        persist_and_read_back(receipt())


def test_missing_database_fails_closed(monkeypatch):
    import mission_control.hrm_durable_receipt as module

    monkeypatch.setenv("OAP_HRM_DURABLE_WRITES_ENABLED", "true")
    monkeypatch.setattr(module, "_database_config", lambda: (None, None))
    with pytest.raises(ReceiptBlocked, match="hrm_database_unconfigured"):
        persist_and_read_back(receipt())


def test_schema_or_database_error_fails_closed(monkeypatch):
    import psycopg

    import mission_control.hrm_durable_receipt as module

    monkeypatch.setenv("OAP_HRM_DURABLE_WRITES_ENABLED", "true")
    monkeypatch.setattr(
        module,
        "_database_config",
        lambda: ("postgresql://example.invalid/db", "test"),
    )
    monkeypatch.setattr(module, "_ssl_url", lambda value: value)
    monkeypatch.setattr(
        psycopg,
        "connect",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("db unavailable")),
    )
    with pytest.raises(
        ReceiptBlocked, match="receipt_database_unavailable_or_schema_missing"
    ):
        persist_and_read_back(receipt())


def test_changed_payload_same_idempotency_key_keeps_identity_but_changes_checksum():
    first = receipt("sig-stable", "attempt")
    payload = proof_payload()
    payload["human_authority_approved"] = True
    second = receipt("sig-stable", "attempt", payload)
    assert first.receipt_id == second.receipt_id
    assert first.checksum != second.checksum
