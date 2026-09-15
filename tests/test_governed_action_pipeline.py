from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest

from mission_control import governed_action_pipeline as pipeline
from mission_control.hrm_agent_lifecycle import BODY_7, MIND_7, SOUL_7


def _approval_row(identity_id: str) -> tuple[object, ...]:
    now = datetime.now(timezone.utc)
    return (
        str(uuid.uuid4()),
        str(uuid.uuid4()),
        identity_id,
        0,
        "APPROVED",
        now,
        now + timedelta(minutes=30),
        "digest",
        "nonce",
        "signature",
    )


def _checks() -> dict[str, dict[str, bool]]:
    return {
        "mind": {name: True for name in MIND_7},
        "body": {name: True for name in BODY_7},
        "soul": {name: True for name in SOUL_7},
    }


def test_authorize_action_requires_registered_action_and_human_approval(monkeypatch):
    request_id = str(uuid.uuid4())
    identity_id = str(uuid.uuid4())
    row = _approval_row(identity_id)
    monkeypatch.setattr(pipeline, "_approval_row", lambda _request_id: row)
    monkeypatch.setattr(
        pipeline,
        "_approval_valid",
        lambda _row, *, identity_id: identity_id == str(row[2]),
    )

    authorized = pipeline.authorize_action(
        signal_id="signal-1",
        request_id=request_id,
        human_authority_identity_id=identity_id,
        action_name="SYNC_INTERNAL_RECORD",
        guardian_passed=True,
        judgement_consistent=True,
    )

    assert authorized["execution_authorized"] is True
    assert authorized["execution_performed"] is False
    assert authorized["authority_transferred"] is False
    assert authorized["action_policy"]["external"] is False
    assert authorized["stages"] == pipeline.CANONICAL_STAGES


def test_authorize_action_rejects_caller_invented_action():
    with pytest.raises(pipeline.ActionBlocked, match="registered_action_required"):
        pipeline.authorize_action(
            signal_id="signal-1",
            request_id=str(uuid.uuid4()),
            human_authority_identity_id=str(uuid.uuid4()),
            action_name="DEPLOY_ANYTHING",
            guardian_passed=True,
            judgement_consistent=True,
        )


def test_authorize_action_fails_closed_without_guardian():
    with pytest.raises(pipeline.ActionBlocked, match="guardian_gate_required"):
        pipeline.authorize_action(
            signal_id="signal-1",
            request_id=str(uuid.uuid4()),
            human_authority_identity_id=str(uuid.uuid4()),
            action_name="SYNC_INTERNAL_RECORD",
            guardian_passed=False,
            judgement_consistent=True,
        )


def test_record_outcome_requires_all_21_checks_and_durable_readback(monkeypatch):
    authorization = {
        "signal_id": "signal-1",
        "request_id": str(uuid.uuid4()),
        "action_name": "SYNC_INTERNAL_RECORD",
        "approval_receipt_id": str(uuid.uuid4()),
        "execution_authorized": True,
        "authority_transferred": False,
    }
    monkeypatch.setattr(
        pipeline,
        "persist_and_read_back",
        lambda receipt: {
            "receipt_id": receipt.receipt_id,
            "checksum": receipt.checksum,
            "write_verified": True,
            "read_back_verified": True,
            "authority_transferred": False,
            "secret_exposed": False,
        },
    )

    result = pipeline.record_action_outcome(
        authorization,
        idempotency_key="action-1",
        action_performed=True,
        evidence_proven=True,
        checks=_checks(),
    )

    assert result["pipeline_complete"] is True
    assert result["stage"] == "HRM_RECEIPT"
    assert result["write_verified"] is True
    assert result["read_back_verified"] is True
    assert result["authority_transferred"] is False


def test_record_outcome_rejects_incomplete_body_plane():
    checks = _checks()
    checks["body"]["verification"] = False
    with pytest.raises(pipeline.ActionBlocked, match="body_proof_incomplete"):
        pipeline.record_action_outcome(
            {
                "signal_id": "signal-1",
                "request_id": str(uuid.uuid4()),
                "action_name": "SYNC_INTERNAL_RECORD",
                "approval_receipt_id": str(uuid.uuid4()),
                "execution_authorized": True,
                "authority_transferred": False,
            },
            idempotency_key="action-1",
            action_performed=True,
            evidence_proven=True,
            checks=checks,
        )
