from __future__ import annotations

import uuid

import pytest

from mission_control import internal_record_executor as executor


def _authorization(identity_id: str) -> dict[str, object]:
    _ = identity_id
    return {
        "signal_id": "all-in-ai:test",
        "request_id": str(uuid.uuid4()),
        "action_name": "SYNC_INTERNAL_RECORD",
        "action_policy": {
            "external": False,
            "reversible": True,
            "authority_change": False,
        },
        "approval_receipt_id": str(uuid.uuid4()),
        "execution_authorized": True,
        "execution_performed": False,
        "authority_transferred": False,
        "human_authority_final": True,
        "stages": (
            "SIGNAL",
            "AGENTS",
            "JUDGEMENT",
            "GUARDIAN",
            "HUMAN_AUTHORITY",
            "ACTION",
            "HRM_RECEIPT",
        ),
    }


class _Result:
    def __init__(self, row=None):
        self._row = row

    def fetchone(self):
        return self._row


class _Connection:
    def __init__(self, *, identity_id: str, record_id: str):
        self.identity_id = identity_id
        self.record_id = record_id
        self.status = "draft"
        self.workspace_id = "governance"
        self.title = "Founder note"
        self.body = "Keep this exact content."
        self.audit = []
        self.committed = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, sql, params=None):
        params = params or ()
        if "pg_advisory_xact_lock" in sql:
            return _Result((1,))
        if "FROM oap_workspace_records" in sql and "FOR UPDATE" in sql:
            record, identity = params
            if record != self.record_id or identity != self.identity_id:
                return _Result(None)
            return _Result(
                (self.workspace_id, self.title, self.body, self.status)
            )
        if "metadata->>'idempotency_key'" in sql:
            return _Result(None)
        if "UPDATE oap_workspace_records" in sql:
            target, record, identity, expected = params
            if (
                record != self.record_id
                or identity != self.identity_id
                or self.status != expected
            ):
                return _Result(None)
            self.status = target
            return _Result(
                (self.workspace_id, self.title, self.body, self.status)
            )
        if "FROM oap_workspace_records" in sql:
            record, identity = params
            if record != self.record_id or identity != self.identity_id:
                return _Result(None)
            return _Result(
                (self.workspace_id, self.title, self.body, self.status)
            )
        if "SELECT curr_hash FROM audit_events" in sql:
            return _Result(None)
        if "INSERT INTO audit_events" in sql:
            self.audit.append(params)
            return _Result((1,))
        raise AssertionError(f"unexpected SQL: {sql}")

    def commit(self):
        self.committed = True


def test_executor_changes_status_only_and_proves_readback(monkeypatch):
    identity = str(uuid.uuid4())
    record = str(uuid.uuid4())
    connection = _Connection(identity_id=identity, record_id=record)
    monkeypatch.setattr(
        executor.postgres_db,
        "connect",
        lambda: connection,
    )
    monkeypatch.setattr(
        executor.governed_action_pipeline,
        "record_action_outcome",
        lambda authorization, **kwargs: {
            "pipeline_complete": True,
            "stage": "HRM_RECEIPT",
            "write_verified": True,
            "read_back_verified": True,
            "authority_transferred": False,
        },
    )

    result = executor.execute(
        _authorization(identity),
        identity_id=identity,
        record_id=record,
        expected_status="draft",
        target_status="active",
    )

    assert connection.status == "active"
    assert connection.title == "Founder note"
    assert connection.body == "Keep this exact content."
    assert connection.committed is True
    assert len(connection.audit) == 1
    assert result["content_unchanged"] is True
    assert result["status_readback_verified"] is True
    assert result["action_performed"] is True
    assert result["evidence_proven"] is True
    assert result["external_side_effect"] is False
    assert result["financial_side_effect"] is False
    assert result["authority_transferred"] is False
    assert result["rollback_token"]["target_status"] == "draft"
    assert result["outcome_receipt"]["pipeline_complete"] is True
    assert all(
        all(plane.values())
        for plane in result["governance_checks"].values()
    )


def test_wrong_owner_fails_closed(monkeypatch):
    identity = str(uuid.uuid4())
    other = str(uuid.uuid4())
    record = str(uuid.uuid4())
    connection = _Connection(identity_id=identity, record_id=record)
    monkeypatch.setattr(executor.postgres_db, "connect", lambda: connection)

    with pytest.raises(
        executor.ExecutionBlocked,
        match="owner_scoped_record_not_found",
    ):
        executor.execute(
            _authorization(other),
            identity_id=other,
            record_id=record,
            expected_status="draft",
            target_status="active",
        )


def test_stale_status_fails_closed(monkeypatch):
    identity = str(uuid.uuid4())
    record = str(uuid.uuid4())
    connection = _Connection(identity_id=identity, record_id=record)
    connection.status = "active"
    monkeypatch.setattr(executor.postgres_db, "connect", lambda: connection)

    with pytest.raises(executor.ExecutionBlocked, match="stale_record_status"):
        executor.execute(
            _authorization(identity),
            identity_id=identity,
            record_id=record,
            expected_status="draft",
            target_status="active",
        )


def test_archived_record_never_mutates(monkeypatch):
    identity = str(uuid.uuid4())
    record = str(uuid.uuid4())
    connection = _Connection(identity_id=identity, record_id=record)
    connection.status = "archived"
    monkeypatch.setattr(executor.postgres_db, "connect", lambda: connection)

    with pytest.raises(executor.ExecutionBlocked, match="archived_record_immutable"):
        executor.execute(
            _authorization(identity),
            identity_id=identity,
            record_id=record,
            expected_status="draft",
            target_status="active",
        )


def test_executor_requires_authorized_reversible_internal_action():
    identity = str(uuid.uuid4())
    authorization = _authorization(identity)
    authorization["execution_authorized"] = False

    with pytest.raises(
        executor.ExecutionBlocked,
        match="execution_authorization_required",
    ):
        executor._validate_authorization(
            authorization,
            identity_id=identity,
        )

    authorization = _authorization(identity)
    authorization["action_policy"] = {
        "external": True,
        "reversible": True,
        "authority_change": False,
    }
    with pytest.raises(executor.ExecutionBlocked, match="external_action_forbidden"):
        executor._validate_authorization(
            authorization,
            identity_id=identity,
        )


def test_executor_rejects_noop_and_archived_target():
    identity = str(uuid.uuid4())
    record = str(uuid.uuid4())

    with pytest.raises(ValueError, match="status_transition_required"):
        executor.execute(
            _authorization(identity),
            identity_id=identity,
            record_id=record,
            expected_status="draft",
            target_status="draft",
        )

    with pytest.raises(ValueError, match="invalid_target_status"):
        executor.execute(
            _authorization(identity),
            identity_id=identity,
            record_id=record,
            expected_status="draft",
            target_status="archived",
        )


def test_executor_status_is_narrow_and_non_financial():
    state = executor.status()
    assert state["registered_action"] == "SYNC_INTERNAL_RECORD"
    assert state["owner_scoped"] is True
    assert state["body_mutation_allowed"] is False
    assert state["title_mutation_allowed"] is False
    assert state["archived_mutation_allowed"] is False
    assert state["external_side_effects_allowed"] is False
    assert state["financial_side_effects_allowed"] is False
    assert state["reversible"] is True
    assert state["human_authority_final"] is True



def test_rollback_requires_exact_post_action_hash(monkeypatch):
    identity = str(uuid.uuid4())
    record = str(uuid.uuid4())
    authorization = _authorization(identity)
    expected_after = executor._proof_hash(
        {
            "workspace_id": "governance",
            "title": "Founder note",
            "body": "Keep this exact content.",
            "status": "active",
        }
    )
    expected_before = executor._proof_hash(
        {
            "workspace_id": "governance",
            "title": "Founder note",
            "body": "Keep this exact content.",
            "status": "draft",
        }
    )
    observed = {}

    def _execute(auth, **kwargs):
        observed["authorization"] = auth
        observed.update(kwargs)
        return {
            "after_hash": expected_before,
            "outcome_receipt": {
                "write_verified": True,
                "read_back_verified": True,
            },
        }

    monkeypatch.setattr(executor, "execute", _execute)

    result = executor.rollback(
        authorization,
        identity_id=identity,
        rollback_token={
            "origin_request_id": str(uuid.uuid4()),
            "record_id": record,
            "expected_status": "active",
            "target_status": "draft",
            "before_hash": expected_before,
            "after_hash": expected_after,
        },
    )

    assert observed["expected_current_hash"] == expected_after
    assert observed["expected_result_hash"] == expected_before
    assert observed["expected_status"] == "active"
    assert observed["target_status"] == "draft"
    assert result["rollback_verified"] is True
    assert result["restored_hash"] == expected_before


def test_rollback_rejects_bad_before_hash():
    identity = str(uuid.uuid4())
    with pytest.raises(ValueError, match="invalid_rollback_before_hash"):
        executor.rollback(
            _authorization(identity),
            identity_id=identity,
            rollback_token={
                "origin_request_id": str(uuid.uuid4()),
                "record_id": str(uuid.uuid4()),
                "expected_status": "active",
                "target_status": "draft",
                "before_hash": "bad",
                "after_hash": "a" * 64,
            },
        )



def test_rollback_wrong_restoration_hash_blocks_before_any_write(monkeypatch):
    identity = str(uuid.uuid4())
    record = str(uuid.uuid4())
    connection = _Connection(identity_id=identity, record_id=record)
    connection.status = "active"
    monkeypatch.setattr(executor.postgres_db, "connect", lambda: connection)
    expected_after = executor._proof_hash({
        "workspace_id": connection.workspace_id,
        "title": connection.title,
        "body": connection.body,
        "status": "active",
    })
    expected_before = executor._proof_hash({
        "workspace_id": connection.workspace_id,
        "title": connection.title,
        "body": connection.body,
        "status": "draft",
    })
    # A well-formed forged before_hash used to fail only AFTER the executor
    # had changed status, inserted audit evidence and committed its outcome.
    forged_before = "f" * 64 if expected_before != "f" * 64 else "e" * 64
    with pytest.raises(
        executor.ExecutionBlocked, match="rollback_restoration_hash_mismatch",
    ):
        executor.rollback(
            _authorization(identity),
            identity_id=identity,
            rollback_token={
                "origin_request_id": str(uuid.uuid4()),
                "record_id": record,
                "expected_status": "active",
                "target_status": "draft",
                "before_hash": forged_before,
                "after_hash": expected_after,
            },
        )
    assert connection.status == "active"
    assert connection.audit == []
    assert connection.committed is False


def test_rollback_correct_hash_changes_only_status_after_readback(monkeypatch):
    identity = str(uuid.uuid4())
    record = str(uuid.uuid4())
    connection = _Connection(identity_id=identity, record_id=record)
    connection.status = "active"
    monkeypatch.setattr(executor.postgres_db, "connect", lambda: connection)
    monkeypatch.setattr(
        executor.governed_action_pipeline, "record_action_outcome",
        lambda authorization, **kwargs: {
            "pipeline_complete": True,
            "stage": "HRM_RECEIPT",
            "write_verified": True,
            "read_back_verified": True,
            "human_authority_final": True,
        },
    )
    expected_after = executor._proof_hash({
        "workspace_id": connection.workspace_id,
        "title": connection.title,
        "body": connection.body,
        "status": "active",
    })
    expected_before = executor._proof_hash({
        "workspace_id": connection.workspace_id,
        "title": connection.title,
        "body": connection.body,
        "status": "draft",
    })
    result = executor.rollback(
        _authorization(identity),
        identity_id=identity,
        rollback_token={
            "origin_request_id": str(uuid.uuid4()),
            "record_id": record,
            "expected_status": "active",
            "target_status": "draft",
            "before_hash": expected_before,
            "after_hash": expected_after,
        },
    )
    assert connection.status == "draft"
    assert connection.committed is True
    assert len(connection.audit) == 1
    assert connection.title == "Founder note"
    assert connection.body == "Keep this exact content."
    assert result["rollback_verified"] is True
    assert result["restored_hash"] == expected_before



def test_rollback_cannot_reuse_original_execution_review_even_with_valid_hash(monkeypatch):
    identity = str(uuid.uuid4())
    record = str(uuid.uuid4())
    connection = _Connection(identity_id=identity, record_id=record)
    connection.status = "active"
    monkeypatch.setattr(executor.postgres_db, "connect", lambda: connection)
    authorization = _authorization(identity)
    token = {
        "origin_request_id": authorization["request_id"],
        "record_id": record,
        "expected_status": "active",
        "target_status": "draft",
        "after_hash": executor._proof_hash({
            "workspace_id": connection.workspace_id,
            "title": connection.title, "body": connection.body,
            "status": "active",
        }),
        "before_hash": executor._proof_hash({
            "workspace_id": connection.workspace_id,
            "title": connection.title, "body": connection.body,
            "status": "draft",
        }),
    }
    with pytest.raises(executor.ExecutionBlocked, match="fresh_rollback_review_required"):
        executor.rollback(authorization, identity_id=identity, rollback_token=token)
    assert connection.status == "active"
    assert connection.audit == []
    assert connection.committed is False


def test_rollback_missing_origin_request_fails_before_mutation(monkeypatch):
    identity = str(uuid.uuid4())
    record = str(uuid.uuid4())
    connection = _Connection(identity_id=identity, record_id=record)
    connection.status = "active"
    monkeypatch.setattr(executor.postgres_db, "connect", lambda: connection)
    with pytest.raises(ValueError, match="invalid_rollback_origin_request_id"):
        executor.rollback(_authorization(identity), identity_id=identity, rollback_token={
            "record_id": record, "expected_status": "active",
            "target_status": "draft", "before_hash": "a" * 64,
            "after_hash": "b" * 64,
        })
    assert connection.status == "active"
    assert connection.audit == []
    assert connection.committed is False
