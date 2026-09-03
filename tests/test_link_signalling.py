from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest

from mission_control import link_signalling, link_signalling_routes


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


def test_signalling_schema_is_explicit_ephemeral_and_media_free():
    dry_run = link_signalling.init_schema(dry_run=True)
    joined = "\n".join(dry_run["statements"])

    assert dry_run["version"] == "link_signalling_v1"
    assert dry_run["applied"] is False
    assert "link_signalling_events" in joined
    assert "INTERVAL '5 minutes'" in joined
    assert "offer" in joined and "answer" in joined and "ice" in joined and "hangup" in joined
    assert "payload JSONB" in joined
    assert "octet_length(payload::text) <= 32768" in joined
    assert "media" not in joined.casefold()
    assert link_signalling.EVENT_TTL_MINUTES == 5
    assert link_signalling.MAX_PAYLOAD_BYTES == 32 * 1024


def test_signalling_rejects_bad_event_and_large_payload_before_database():
    with pytest.raises(ValueError, match="invalid_signalling_event"):
        link_signalling.publish(
            uuid.uuid4(),
            uuid.uuid4(),
            session_id=uuid.uuid4(),
            event_type="record_call",
            payload={},
        )

    with pytest.raises(ValueError, match="signalling_payload_too_large"):
        link_signalling.publish(
            uuid.uuid4(),
            uuid.uuid4(),
            session_id=uuid.uuid4(),
            event_type="offer",
            payload={"sdp": "x" * (link_signalling.MAX_PAYLOAD_BYTES + 1)},
        )


def test_signalling_block_guard_runs_before_database(monkeypatch):
    monkeypatch.setattr(
        link_signalling.linkup_safety, "blocked_between", lambda _first, _second: True
    )
    monkeypatch.setattr(
        link_signalling.postgres_db,
        "connect",
        lambda *args, **kwargs: pytest.fail("database must not be reached for blocked pair"),
    )

    with pytest.raises(ValueError, match="link_blocked"):
        link_signalling.publish(
            uuid.uuid4(),
            uuid.uuid4(),
            session_id=uuid.uuid4(),
            event_type="offer",
            payload={"sdp": "bounded"},
        )


def test_signalling_requires_an_accepted_nonexpired_link(monkeypatch):
    monkeypatch.setattr(
        link_signalling.linkup_safety, "blocked_between", lambda _first, _second: False
    )
    connection = _Connection(
        lambda query, _params: _Result(row=None)
        if "FROM link_relationships" in query
        else pytest.fail(f"unexpected query after missing accepted Link: {query}")
    )
    monkeypatch.setattr(
        link_signalling.postgres_db, "connect", lambda *args, **kwargs: _Context(connection)
    )

    with pytest.raises(ValueError, match="accepted_link_required"):
        link_signalling.publish(
            uuid.uuid4(),
            uuid.uuid4(),
            session_id=uuid.uuid4(),
            event_type="offer",
            payload={"sdp": "bounded"},
        )

    accepted_query = next(query for query, _ in connection.calls if "FROM link_relationships" in query)
    assert "status='accepted'" in accepted_query
    assert "expires_at>CURRENT_TIMESTAMP" in accepted_query


def test_publish_is_bounded_and_purges_expired_events(monkeypatch):
    sender = str(uuid.uuid4())
    recipient = str(uuid.uuid4())
    session_id = str(uuid.uuid4())
    event_id = str(uuid.uuid4())
    monkeypatch.setattr(
        link_signalling.linkup_safety, "blocked_between", lambda _first, _second: False
    )

    def handler(query, _params):
        if "FROM link_relationships" in query:
            return _Result(row=(1,))
        if "SELECT COUNT(*) FROM link_signalling_events" in query:
            return _Result(row=(0,))
        if query.startswith("DELETE FROM link_signalling_events WHERE expires_at"):
            return _Result(rowcount=2)
        if query.startswith("INSERT INTO link_signalling_events"):
            return _Result(row=(event_id,))
        raise AssertionError(f"unexpected query: {query}")

    connection = _Connection(handler)
    monkeypatch.setattr(
        link_signalling.postgres_db, "connect", lambda *args, **kwargs: _Context(connection)
    )

    created = link_signalling.publish(
        sender,
        recipient,
        session_id=session_id,
        event_type="offer",
        payload={"sdp": "offer-data"},
    )

    assert created == event_id
    assert connection.committed is True
    assert any("expires_at<=CURRENT_TIMESTAMP" in query for query, _ in connection.calls)
    insert_call = next(call for call in connection.calls if call[0].startswith("INSERT INTO"))
    assert insert_call[1][0:4] == (session_id, sender, recipient, "offer")


def test_list_events_is_scoped_to_recipient_and_session(monkeypatch):
    identity = str(uuid.uuid4())
    sender = str(uuid.uuid4())
    session_id = str(uuid.uuid4())
    event_id = str(uuid.uuid4())
    created_at = datetime.now(timezone.utc)

    def handler(query, params):
        assert "WHERE recipient_id=%s AND session_id=%s" in query
        assert params[0] == identity
        assert params[1] == session_id
        return _Result(
            rows=[(event_id, sender, "ice", {"candidate": "abc"}, created_at)]
        )

    connection = _Connection(handler)
    monkeypatch.setattr(
        link_signalling.postgres_db, "connect", lambda *args, **kwargs: _Context(connection)
    )

    events = link_signalling.list_events(identity, session_id=session_id)

    assert events == [
        {
            "event_id": event_id,
            "sender_id": sender,
            "event_type": "ice",
            "payload": {"candidate": "abc"},
            "created_at": created_at.isoformat(),
        }
    ]


def test_acknowledge_can_delete_only_the_recipient_event(monkeypatch):
    identity = str(uuid.uuid4())
    event_id = str(uuid.uuid4())

    def handler(query, params):
        assert "WHERE id=%s AND recipient_id=%s" in query
        assert params == (event_id, identity)
        return _Result(row=(event_id,))

    connection = _Connection(handler)
    monkeypatch.setattr(
        link_signalling.postgres_db, "connect", lambda *args, **kwargs: _Context(connection)
    )

    assert link_signalling.acknowledge(identity, event_id) is True
    assert connection.committed is True


def test_signalling_routes_are_authenticated_and_fail_closed(
    client, anonymous_client, monkeypatch
):
    anonymous = anonymous_client.get("/linkup/signalling/status")
    assert anonymous.status_code == 401

    monkeypatch.setattr(
        link_signalling_routes.link_signalling,
        "status",
        lambda: {"configured": True, "ready": False},
    )
    response = client.get("/linkup/signalling/status")
    assert response.status_code == 200
    assert response.get_json() == {"ready": False}
    assert response.headers["Cache-Control"] == "no-store"


def test_signalling_publish_route_requires_csrf(client):
    response = client.post(
        "/linkup/signalling/events",
        json={
            "recipient_id": str(uuid.uuid4()),
            "session_id": str(uuid.uuid4()),
            "event_type": "offer",
            "payload": {"sdp": "bounded"},
        },
    )

    assert response.status_code == 403
    assert response.get_json()["error"]["code"] == "csrf_failed"
