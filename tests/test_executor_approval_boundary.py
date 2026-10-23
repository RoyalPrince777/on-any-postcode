"""Fail-closed approval checks at the bounded executor boundary."""
import uuid
from datetime import UTC, datetime, timedelta

import pytest

from mission_control import internal_record_executor as executor


def _authorization(request, receipt):
    return {
        "execution_authorized": True,
        "execution_performed": False,
        "authority_transferred": False,
        "human_authority_final": True,
        "action_name": "SYNC_INTERNAL_RECORD",
        "action_policy": {
            "external": False,
            "reversible": True,
            "authority_change": False,
        },
        "request_id": request,
        "approval_receipt_id": receipt,
    }


def _row(request, receipt, identity):
    now = datetime.now(UTC)
    return (receipt, request, identity, 0, "APPROVED", now,
            now + timedelta(minutes=10), "digest", "nonce", "signature")


def test_executor_rejects_forged_receipt_identifier(monkeypatch):
    request, receipt, identity = (str(uuid.uuid4()) for _ in range(3))
    monkeypatch.setattr(executor.governed_action_pipeline, "_approval_row",
                        lambda _: _row(request, receipt, identity))
    monkeypatch.setattr(executor.governed_action_pipeline, "_approval_valid",
                        lambda row, *, identity_id: True)
    with pytest.raises(executor.ExecutionBlocked, match="human_authority_approval_invalid"):
        executor._validate_authorization(
            _authorization(request, str(uuid.uuid4())), identity_id=identity
        )


def test_executor_rejects_invalid_signature_or_expiry(monkeypatch):
    request, receipt, identity = (str(uuid.uuid4()) for _ in range(3))
    monkeypatch.setattr(executor.governed_action_pipeline, "_approval_row",
                        lambda _: _row(request, receipt, identity))
    monkeypatch.setattr(executor.governed_action_pipeline, "_approval_valid",
                        lambda row, *, identity_id: False)
    with pytest.raises(executor.ExecutionBlocked, match="human_authority_approval_invalid"):
        executor._validate_authorization(
            _authorization(request, receipt), identity_id=identity
        )


def test_executor_rejects_missing_approval_store(monkeypatch):
    request, receipt, identity = (str(uuid.uuid4()) for _ in range(3))
    def unavailable(_):
        raise RuntimeError("database unavailable")
    monkeypatch.setattr(executor.governed_action_pipeline, "_approval_row", unavailable)
    with pytest.raises(executor.ExecutionBlocked, match="human_authority_approval_unverifiable"):
        executor._validate_authorization(
            _authorization(request, receipt), identity_id=identity
        )
