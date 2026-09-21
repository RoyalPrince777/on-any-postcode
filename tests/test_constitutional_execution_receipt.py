"""Constitutional completion guard for the existing bounded internal action.

These tests do not execute external actions or touch production persistence.
"""
from __future__ import annotations

import uuid

import pytest

from mission_control import governed_action_pipeline as pipeline
from mission_control.hrm_agent_lifecycle import BODY_7, MIND_7, SOUL_7


def _authorization() -> dict[str, object]:
    return {
        "signal_id": "constitutional-signal",
        "request_id": str(uuid.uuid4()),
        "action_name": "SYNC_INTERNAL_RECORD",
        "approval_receipt_id": str(uuid.uuid4()),
        "execution_authorized": True,
        "authority_transferred": False,
    }


def _checks() -> dict[str, dict[str, bool]]:
    return {
        "mind": {name: True for name in MIND_7},
        "body": {name: True for name in BODY_7},
        "soul": {name: True for name in SOUL_7},
    }


def _record(authorization: dict[str, object]) -> dict[str, object]:
    return pipeline.record_action_outcome(
        authorization,
        idempotency_key="constitutional-action-1",
        action_performed=True,
        evidence_proven=True,
        checks=_checks(),
    )


def test_complete_only_after_matching_durable_readback(monkeypatch):
    def verified(receipt):
        return {
            "receipt_id": receipt.receipt_id,
            "checksum": receipt.checksum,
            "write_verified": True,
            "read_back_verified": True,
            "authority_transferred": False,
            "secret_exposed": False,
        }

    monkeypatch.setattr(pipeline, "persist_and_read_back", verified)
    result = _record(_authorization())
    assert result["pipeline_complete"] is True
    assert result["stage"] == "HRM_RECEIPT"
    assert result["human_authority_final"] is True


@pytest.mark.parametrize(
    ("mutation", "label"),
    [
        ({"receipt_id": "wrong-receipt"}, "receipt_mismatch"),
        ({"checksum": "wrong-checksum"}, "checksum_mismatch"),
        ({"write_verified": False}, "write_failed"),
        ({"read_back_verified": False}, "readback_failed"),
        ({"authority_transferred": True}, "authority_transfer"),
        ({"secret_exposed": True}, "secret_exposure"),
    ],
)
def test_incomplete_receipt_cannot_claim_pipeline_complete(monkeypatch, mutation, label):
    def unverified(receipt):
        result = {
            "receipt_id": receipt.receipt_id,
            "checksum": receipt.checksum,
            "write_verified": True,
            "read_back_verified": True,
            "authority_transferred": False,
            "secret_exposed": False,
        }
        result.update(mutation)
        return result

    monkeypatch.setattr(pipeline, "persist_and_read_back", unverified)
    with pytest.raises(pipeline.ActionBlocked, match="receipt_readback_verification_failed"):
        _record(_authorization())


@pytest.mark.parametrize(
    "result",
    [
        None,
        {},
        {"write_verified": True, "read_back_verified": True},
        [],
    ],
)
def test_missing_receipt_proof_fails_closed(monkeypatch, result):
    monkeypatch.setattr(pipeline, "persist_and_read_back", lambda receipt: result)
    with pytest.raises(pipeline.ActionBlocked, match="receipt_readback_verification_failed"):
        _record(_authorization())


def test_missing_evidence_never_calls_persistence(monkeypatch):
    def should_not_write(receipt):
        raise AssertionError("persistence must not be reached")

    monkeypatch.setattr(pipeline, "persist_and_read_back", should_not_write)
    with pytest.raises(pipeline.ActionBlocked, match="action_evidence_required"):
        pipeline.record_action_outcome(
            _authorization(),
            idempotency_key="constitutional-action-1",
            action_performed=True,
            evidence_proven=False,
            checks=_checks(),
        )


def test_unregistered_external_action_never_calls_persistence(monkeypatch):
    def should_not_write(receipt):
        raise AssertionError("persistence must not be reached")

    monkeypatch.setattr(pipeline, "persist_and_read_back", should_not_write)
    authorization = _authorization()
    authorization["action_name"] = "CAPTURE_PAYMENT"
    with pytest.raises(pipeline.ActionBlocked, match="registered_action_required"):
        _record(authorization)
