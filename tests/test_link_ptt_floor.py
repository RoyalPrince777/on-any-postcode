"""Adversarial floor control: session gate, contention, STOP, expiry and CSRF."""
from __future__ import annotations

import uuid

import pytest

from mission_control import link_ptt_floor, link_ptt_routes


class Result:
    def __init__(self, row=None):
        self.row = row

    def fetchone(self):
        return self.row


class Connection:
    def __init__(self, initiator, recipient, *, active=True, previous=None):
        self.initiator = initiator
        self.recipient = recipient
        self.active = active
        self.previous = previous
        self.queries = []
        self.committed = False

    def execute(self, query, params=None):
        sql = " ".join(query.split())
        self.queries.append((sql, params))
        if "FROM link_call_sessions" in sql:
            assert "state='active'" in sql and "FOR UPDATE" in sql
            return Result((self.initiator, self.recipient) if self.active else None)
        if sql.startswith("SELECT holder_id,lease_until"):
            return Result(self.previous)
        if sql.startswith("INSERT INTO link_ptt_floor"):
            assert "ON CONFLICT(session_id)" in sql
            assert params[2] == link_ptt_floor.LEASE_SECONDS
            return Result()
        if sql.startswith("DELETE FROM link_ptt_floor"):
            return Result()
        raise AssertionError(f"unexpected query: {sql}")

    def commit(self):
        self.committed = True


class Context:
    def __init__(self, db):
        self.db = db

    def __enter__(self):
        return self.db

    def __exit__(self, _kind, _error, _traceback):
        return False


def setup(monkeypatch, connection):
    monkeypatch.setattr(link_ptt_floor, "_require_ready", lambda: None)
    monkeypatch.setattr(
        link_ptt_floor.postgres_db, "connect", lambda **_kwargs: Context(connection)
    )
    monkeypatch.setattr(
        link_ptt_floor.link_call_audit, "_relationship_guard", lambda *_args: None
    )
    monkeypatch.setattr(
        link_ptt_floor.link_call_audit, "_youth_guard", lambda *_args: None
    )


def test_floor_schema_is_explicit_and_never_claims_media_control():
    with pytest.raises(PermissionError, match="explicit_confirmation_required"):
        link_ptt_floor.init_schema()
    dry = link_ptt_floor.init_schema(dry_run=True)
    assert dry["applied"] is False
    assert "REFERENCES link_call_sessions(session_id)" in dry["statements"][0]
    assert "lease_until" in dry["statements"][0]
    assert link_ptt_floor.LEASE_SECONDS == 8


def test_floor_denies_ringing_and_unrelated_sessions_before_lease_query(monkeypatch):
    first, second, session = (str(uuid.uuid4()) for _ in range(3))
    connection = Connection(first, second, active=False)
    setup(monkeypatch, connection)
    with pytest.raises(ValueError, match="active_ptt_call_required"):
        link_ptt_floor.floor(first, session, action="acquire")
    assert len(connection.queries) == 1
    assert not connection.committed


def test_floor_grants_one_holder_and_renews_own_lease(monkeypatch):
    first, second, session = (str(uuid.uuid4()) for _ in range(3))
    for previous in (None, (first, True), (second, False)):
        db = Connection(first, second, previous=previous)
        setup(monkeypatch, db)
        result = link_ptt_floor.floor(first, session, action="acquire")
        assert result == {
            "granted": True, "holder_id": first, "lease_seconds": 8
        }
        assert db.committed
        assert any(sql.startswith("INSERT INTO link_ptt_floor") for sql, _ in db.queries)


def test_floor_refuses_second_speaker_and_nonholder_release(monkeypatch):
    first, second, session = (str(uuid.uuid4()) for _ in range(3))
    db = Connection(first, second, previous=(second, True))
    setup(monkeypatch, db)
    with pytest.raises(ValueError, match="ptt_floor_busy"):
        link_ptt_floor.floor(first, session, action="acquire")
    with pytest.raises(ValueError, match="ptt_floor_not_holder"):
        link_ptt_floor.floor(first, session, action="release")
    assert not any(sql.startswith("DELETE FROM") for sql, _ in db.queries)


def test_either_participant_can_server_stop_a_live_floor(monkeypatch):
    first, second, session = (str(uuid.uuid4()) for _ in range(3))
    db = Connection(first, second, previous=(second, True))
    setup(monkeypatch, db)
    result = link_ptt_floor.floor(first, session, action="stop")
    assert result == {"granted": False, "holder_id": None, "stopped": True}
    assert db.committed
    assert any(sql.startswith("DELETE FROM link_ptt_floor") for sql, _ in db.queries)


def test_current_relationship_guard_blocks_floor_mutations(monkeypatch):
    first, second, session = (str(uuid.uuid4()) for _ in range(3))
    db = Connection(first, second)
    setup(monkeypatch, db)

    def blocked(*_args):
        raise ValueError("link_blocked")

    monkeypatch.setattr(link_ptt_floor.link_call_audit, "_relationship_guard", blocked)
    with pytest.raises(ValueError, match="link_blocked"):
        link_ptt_floor.floor(first, session, action="acquire")
    assert len(db.queries) == 1


def test_ptt_floor_route_requires_csrf_and_auth(client, anonymous_client):
    session = str(uuid.uuid4())
    route = f"/linkup/calls/{session}/ptt/floor"
    response = client.post(route, json={"action": "acquire"})
    assert response.status_code == 403
    assert response.get_json()["error"]["code"] == "csrf_failed"
    assert anonymous_client.get("/linkup/ptt/status").status_code in {302, 401, 403}
    assert response.headers["Cache-Control"] == "no-store"


def test_ptt_status_does_not_claim_server_media_enforcement(client, monkeypatch):
    monkeypatch.setattr(
        link_ptt_routes.link_ptt_floor, "status",
        lambda: {"ready": False, "schema_ready": False, "server_controls_media": False},
    )
    result = client.get("/linkup/ptt/status")
    assert result.status_code == 200
    assert result.get_json()["server_controls_media"] is False


def test_invalid_floor_actions_fail_before_db_access(monkeypatch):
    identity, session = str(uuid.uuid4()), str(uuid.uuid4())
    monkeypatch.setattr(link_ptt_floor, "_require_ready", lambda: pytest.fail("invalid actions must be rejected before readiness"))
    for value in (None, [], {}, 1, "unmute", "ACQUIRE"):
        with pytest.raises(ValueError, match="invalid_ptt_action"):
            link_ptt_floor.floor(identity, session, action=value)
