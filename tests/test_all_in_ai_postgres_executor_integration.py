"""Real PostgreSQL rollback atomicity proof for ALL IN's bounded executor.

Only runs with explicit OAP_REAL_POSTGRES_PROOF=1 against the ephemeral CI
PostgreSQL service. Never authorises or migrates a production database.
"""
from __future__ import annotations

import os
from uuid import uuid4

import pytest

from mission_control import internal_record_executor as executor
from mission_control import postgres_db

pytestmark = pytest.mark.skipif(
    os.environ.get("OAP_REAL_POSTGRES_PROOF") != "1",
    reason="isolated PostgreSQL proof runs only in existing CI database step",
)


def _authorization(request_id: str, signal_id: str) -> dict[str, object]:
    return {
        "signal_id": signal_id,
        "request_id": request_id,
        "action_name": "SYNC_INTERNAL_RECORD",
        "action_policy": {
            "external": False, "reversible": True, "authority_change": False,
        },
        "approval_receipt_id": str(uuid4()),
        "execution_authorized": True,
        "execution_performed": False,
        "authority_transferred": False,
        "human_authority_final": True,
        "stages": (
            "SIGNAL", "AGENTS", "JUDGEMENT", "GUARDIAN",
            "HUMAN_AUTHORITY", "ACTION", "HRM_RECEIPT",
        ),
    }


def test_real_postgres_atomic_rollback_forged_token_and_hrm_receipts(monkeypatch):
    # An explicit test-only schema on CI's ephemeral PostgreSQL database.
    # The app never creates receipt schema during runtime execution.
    assert postgres_db.init_postgres(assume_yes=True)["initialized"] is True
    with postgres_db.connect() as connection:
        connection.execute(
            """CREATE TABLE IF NOT EXISTS oap_hrm_receipts (
                receipt_id UUID PRIMARY KEY,
                signal_id TEXT NOT NULL,
                checksum TEXT NOT NULL,
                payload JSONB NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
            )"""
        )
        connection.commit()
    monkeypatch.setenv("OAP_HRM_DURABLE_WRITES_ENABLED", "1")

    owner, record = str(uuid4()), str(uuid4())
    execution_request, recovery_request = str(uuid4()), str(uuid4())
    signal = f"all-in-ai:postgres-proof:{owner}"
    title, body = "Owner-scoped CI note", "Preserve this exact note body."
    with postgres_db.connect() as connection:
        connection.execute(
            """INSERT INTO users(id,email,username,display_name,status)
               VALUES (%s,%s,%s,'CI Founder','active')""",
            (owner, f"{owner}@example.invalid", f"ci-{owner[:8]}"),
        )
        connection.execute(
            """INSERT INTO oap_workspace_records(
                   record_id,identity_id,workspace_id,title,body,status)
               VALUES (%s,%s,'governance',%s,%s,'draft')""",
            (record, owner, title, body),
        )
        connection.commit()

    first = executor.execute(
        _authorization(execution_request, signal),
        identity_id=owner,
        record_id=record,
        expected_status="draft",
        target_status="active",
    )
    assert first["action_performed"] is True
    assert first["status_readback_verified"] is True
    assert first["outcome_receipt"]["write_verified"] is True
    assert first["outcome_receipt"]["read_back_verified"] is True
    token = first["rollback_token"]
    assert token["origin_request_id"] == execution_request

    def read_state():
        with postgres_db.connect(readonly=True) as connection:
            row = connection.execute(
                """SELECT status,title,body FROM oap_workspace_records
                   WHERE record_id=%s AND identity_id=%s""",
                (record, owner),
            ).fetchone()
            audit_count = connection.execute(
                """SELECT count(*) FROM audit_events
                   WHERE action=%s AND actor_id=%s AND target=%s""",
                (executor._AUDIT_ACTION, owner, f"workspace_record:{record}"),
            ).fetchone()[0]
            hrm_count = connection.execute(
                "SELECT count(*) FROM oap_hrm_receipts WHERE signal_id=%s",
                (signal,),
            ).fetchone()[0]
            return tuple(row), int(audit_count), int(hrm_count)

    assert read_state() == (("active", title, body), 1, 1)
    fresh_approval = _authorization(recovery_request, signal)

    # The forged 64-char before_hash was previously checked only AFTER COMMIT.
    wrong = {**token, "before_hash": "f" * 64}
    if wrong["before_hash"] == token["before_hash"]:
        wrong["before_hash"] = "e" * 64
    with pytest.raises(
        executor.ExecutionBlocked, match="rollback_restoration_hash_mismatch",
    ):
        executor.rollback(
            fresh_approval, identity_id=owner, rollback_token=wrong,
        )
    assert read_state() == (("active", title, body), 1, 1)

    # Even a hash-correct token with a forged origin cannot assert its own
    # authority: previous immutable audit must match the origin request.
    forged_origin = {**token, "origin_request_id": str(uuid4())}
    with pytest.raises(
        executor.ExecutionBlocked, match="rollback_origin_audit_mismatch",
    ):
        executor.rollback(
            fresh_approval, identity_id=owner, rollback_token=forged_origin,
        )
    assert read_state() == (("active", title, body), 1, 1)

    # The originating execution request cannot approve its own undo.
    with pytest.raises(
        executor.ExecutionBlocked, match="fresh_rollback_review_required",
    ):
        executor.rollback(
            _authorization(execution_request, signal),
            identity_id=owner,
            rollback_token=token,
        )
    assert read_state() == (("active", title, body), 1, 1)

    restored = executor.rollback(
        fresh_approval, identity_id=owner, rollback_token=token,
    )
    assert restored["rollback_verified"] is True
    assert restored["after_hash"] == token["before_hash"]
    assert restored["restored_hash"] == token["before_hash"]
    assert restored["outcome_receipt"]["write_verified"] is True
    assert restored["outcome_receipt"]["read_back_verified"] is True
    assert read_state() == (("draft", title, body), 2, 2)

    # Stale/replayed recovery cannot duplicate an outcome.
    with pytest.raises(executor.ExecutionBlocked, match="stale_record_status"):
        executor.rollback(
            _authorization(str(uuid4()), signal),
            identity_id=owner, rollback_token=token,
        )
    assert read_state() == (("draft", title, body), 2, 2)
