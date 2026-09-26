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
