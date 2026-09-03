from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest

from mission_control import link_call_audit, link_call_routes


class _Result:
    def __init__(self, row=None, rows=None, rowcount=0):
        self._row = row
        self._rows = rows or []
        self.rowcount = rowcount

    def fetchone(self):
        return self._row

    def fetchall(self):
        return self._rows


class _Connection:
    def __init__(self, handler):
        self.handler = handler
        self.calls = []
        self.committed = False

    def execute(self, query, params=None):
        normalized = " ".join(str(query).split())
        self.calls.append((normalized, params))
        return self.handler(normalized, params)

    def commit(self):
        self.committed = True


class _Context:
    def __init__(self, connection):
        self.connection = connection

    def __enter__(self):
        return self.connection

    def __exit__(self, exc_type, exc, tb):
        return False


def _ready(monkeypatch, days=7):
    monkeypatch.setattr(
        link_call_audit,
        "status",
        lambda: {
            "configured": True,
            "schema_ready": True,
            "retention_configured": True,
            "retention_days": days,
            "records_media": False,
            "ready": True,
        },
    )


def test_call_audit_schema_is_explicit_bounded_and_media_free():
    dry_run = link_call_audit.init_schema(dry_run=True)
    joined = "\n".join(dry_run["statements"]).casefold()

    assert dry_run["version"] == "link_call_audit_v1"
    assert dry_run["applied"] is False
    assert "link_call_sessions" in joined
    assert "call" in joined and "face_up" in joined
    assert "expires_at" in joined
    for forbidden in ("audio", "video", "sdp", "ice", "transcript", "fingerprint"):
        assert forbidden not in joined


def test_retention_must_be_explicit_and_bounded(monkeypatch):
    monkeypatch.delenv("OAP_LINK_CALL_AUDIT_RETENTION_DAYS", raising=False)
    assert link_call_audit.retention_days() is None
    monkeypatch.setenv("OAP_LINK_CALL_AUDIT_RETENTION_DAYS", "0")
    assert link_call_audit.retention_days() is None
    monkeypatch.setenv("OAP_LINK_CALL_AUDIT_RETENTION_DAYS", "91")
    assert link_call_audit.retention_days() is None
    monkeypatch.setenv("OAP_LINK_CALL_AUDIT_RETENTION_DAYS", "7")
    assert link_call_audit.retention_days() == 7


def test_blocked_call_stops_before_call_database(monkeypatch):
    monkeypatch.setattr(
        link_call_audit.linkup_safety, "blocked_between", lambda _first, _second: True
    )
    monkeypatch.setattr(
        link_call_audit.postgres_db,
        "connect",
        lambda *args, **kwargs: pytest.fail("blocked call must not reach call database"),
    )

    with pytest.raises(ValueError, match="link_blocked"):
        link_call_audit.start_session(uuid.uuid4(), uuid.uuid4(), mode="call")


def test_answer_rechecks_relationship_before_state_transition(monkeypatch):
    _ready(monkeypatch)
    identity = str(uuid.uuid4())
    initiator = str(uuid.uuid4())
    session_id = str(uuid.uuid4())

    def handler(query, _params):
        if query.startswith("SELECT initiator_id FROM link_call_sessions"):
            return _Result(row=(initiator,))
        if query.startswith("UPDATE link_call_sessions"):
            pytest.fail("blocked relationship must not transition call state")
        raise AssertionError(f"unexpected query: {query}")

    connection = _Connection(handler)
    monkeypatch.setattr(
        link_call_audit.postgres_db,
        "connect",
        lambda *args, **kwargs: _Context(connection),
    )
    monkeypatch.setattr(
        link_call_audit.linkup_safety, "blocked_between", lambda _first, _second: True
    )

    with pytest.raises(ValueError, match="link_blocked"):
        link_call_audit.answer_session(identity, session_id)


def test_call_session_signalling_guard_is_pair_scoped(monkeypatch):
    _ready(monkeypatch)
    first = str(uuid.uuid4())
    second = str(uuid.uuid4())
    session_id = str(uuid.uuid4())

    def handler(query, params):
        assert "state IN ('ringing','active')" in query
        assert "LEAST(initiator_id,recipient_id)" in query
        assert params == (session_id, first, second, first, second)
        return _Result(row=(1,))

    connection = _Connection(handler)
    monkeypatch.setattr(
        link_call_audit.postgres_db,
        "connect",
        lambda *args, **kwargs: _Context(connection),
    )

    assert link_call_audit.session_allows_signalling(first, second, session_id) is True


def test_active_call_list_returns_only_bounded_session_metadata(monkeypatch):
    _ready(monkeypatch)
    identity = str(uuid.uuid4())
    peer = str(uuid.uuid4())
    session_id = str(uuid.uuid4())
    started = datetime.now(timezone.utc)

    connection = _Connection(
        lambda _query, _params: _Result(
            rows=[(session_id, peer, identity, "face_up", "ringing", started, None)]
        )
    )
    monkeypatch.setattr(
        link_call_audit.postgres_db,
        "connect",
        lambda *args, **kwargs: _Context(connection),
    )

    sessions = link_call_audit.list_active(identity)

    assert sessions == [
        {
            "session_id": session_id,
            "peer_id": peer,
            "direction": "incoming",
            "mode": "face_up",
            "state": "ringing",
            "started_at": started.isoformat(),
            "answered_at": None,
        }
    ]
    assert "audio" not in str(sessions).casefold()
    assert "video" not in str(sessions).casefold()


def test_call_status_route_is_fail_closed_and_media_free(client, monkeypatch):
    monkeypatch.setattr(
        link_call_routes.link_call_audit,
        "status",
        lambda: {
            "configured": True,
            "schema_ready": False,
            "retention_configured": False,
            "retention_days": None,
            "records_media": False,
            "ready": False,
        },
    )

    response = client.get("/linkup/calls/status")

    assert response.status_code == 200
    assert response.get_json() == {
        "ready": False,
        "records_media": False,
        "retention_configured": False,
        "schema_ready": False,
    }
    assert response.headers["Cache-Control"] == "no-store"


def test_start_call_route_requires_csrf(client):
    response = client.post(
        "/linkup/calls",
        json={"recipient_id": str(uuid.uuid4()), "mode": "call"},
    )

    assert response.status_code == 403
    assert response.get_json()["error"]["code"] == "csrf_failed"
