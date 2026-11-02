from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest

from mission_control import link_circles


class _Result:
    def __init__(self, row=None, rows=None):
        self._row = row
        self._rows = rows or []

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


def test_circle_schema_is_explicit_bounded_and_membership_only():
    dry = link_circles.init_schema(dry_run=True)
    joined = "\n".join(dry["statements"])
    assert dry["version"] == "link_circles_v1"
    assert dry["applied"] is False
    assert "link_circles" in joined
    assert "link_circle_members" in joined
    assert "link_circle_invites" in joined
    assert "link_circle_messages" in joined
    assert "recipient_id" not in joined.casefold()
    assert "media" not in joined.casefold()


def test_bring_in_requires_safe_accepted_link_before_circle_storage(monkeypatch):
    host = str(uuid.uuid4())
    invitee = str(uuid.uuid4())
    circle = str(uuid.uuid4())
    monkeypatch.setattr(link_circles.linkup_safety, "blocked_between", lambda *_args: True)
    monkeypatch.setattr(
        link_circles.postgres_db,
        "connect",
        lambda *args, **kwargs: pytest.fail("Circle DB must not be reached after Block"),
    )
    with pytest.raises(ValueError, match="link_blocked"):
        link_circles.bring_in(host, circle, invitee)


def test_create_circle_persists_host_membership_in_one_transaction(monkeypatch):
    host = str(uuid.uuid4())
    circle = str(uuid.uuid4())

    def handler(query, params):
        if query.startswith("SELECT 1 FROM users"):
            return _Result(row=(1,))
        if query.startswith("INSERT INTO link_circles"):
            assert params == (host, "South London")
            return _Result(row=(circle,))
        if query.startswith("INSERT INTO link_circle_members"):
            assert params == (circle, host)
            return _Result()
        raise AssertionError(query)

    connection = _Connection(handler)
    monkeypatch.setattr(link_circles.postgres_db, "connect", lambda *a, **k: _Context(connection))
    assert link_circles.create_circle(host, "  South   London  ") == circle
    assert connection.committed is True


def test_host_step_out_promotes_oldest_active_member(monkeypatch):
    host = str(uuid.uuid4())
    successor = str(uuid.uuid4())
    circle = str(uuid.uuid4())
    host_membership = str(uuid.uuid4())
    successor_membership = str(uuid.uuid4())

    def handler(query, params):
        if query.startswith("SELECT id,role FROM link_circle_members"):
            return _Result(row=(host_membership, "host"))
        if query.startswith("SELECT id,user_id FROM link_circle_members"):
            return _Result(row=(successor_membership, successor))
        if query.startswith("UPDATE link_circle_members SET role='host'"):
            return _Result()
        if query.startswith("UPDATE link_circles SET host_id="):
            return _Result()
        if query.startswith("UPDATE link_circle_members SET status='left'"):
            return _Result()
        raise AssertionError(query)

    connection = _Connection(handler)
    monkeypatch.setattr(link_circles.postgres_db, "connect", lambda *a, **k: _Context(connection))
    assert link_circles.step_out(host, circle) is True
    assert connection.committed is True


def test_last_host_step_out_closes_circle_and_revokes_pending_invites(monkeypatch):
    host = str(uuid.uuid4())
    circle = str(uuid.uuid4())
    membership = str(uuid.uuid4())

    def handler(query, params):
        if query.startswith("SELECT id,role FROM link_circle_members"):
            return _Result(row=(membership, "host"))
        if query.startswith("SELECT id,user_id FROM link_circle_members"):
            return _Result(row=None)
        if query.startswith("UPDATE link_circles SET status='closed'"):
            return _Result()
        if query.startswith("UPDATE link_circle_invites SET status='revoked'"):
            return _Result()
        if query.startswith("UPDATE link_circle_members SET status='left'"):
            return _Result()
        raise AssertionError(query)

    connection = _Connection(handler)
    monkeypatch.setattr(link_circles.postgres_db, "connect", lambda *a, **k: _Context(connection))
    assert link_circles.step_out(host, circle) is True
    assert connection.committed is True


def test_circle_dashboard_never_returns_message_or_media_content(monkeypatch):
    identity = str(uuid.uuid4())
    circle = str(uuid.uuid4())
    now = datetime.now(UTC)

    def handler(query, params):
        if query.startswith("SELECT c.id,c.name"):
            return _Result(rows=[(circle, "Family", identity, "host", now)])
        if query.startswith("SELECT i.id,i.circle_id"):
            return _Result(rows=[])
        if query.startswith("SELECT m.user_id,m.role"):
            return _Result(rows=[(identity, "host", "Founder", now)])
        raise AssertionError(query)

    connection = _Connection(handler)
    monkeypatch.setattr(link_circles.postgres_db, "connect", lambda *a, **k: _Context(connection))
    data = link_circles.dashboard(identity)
    flattened = repr(data).casefold()
    assert "message" not in flattened
    assert "media" not in flattened


def test_circle_status_route_denies_anonymous_user(anonymous_client):
    assert anonymous_client.get("/linkup/circles/status").status_code == 401


def test_circle_page_exists_for_member_and_mutation_requires_csrf(client):
    assert client.get("/linkup/circles").status_code == 200
    assert client.post("/linkup/circles", data={"name": "Family"}).status_code == 403


def test_invite_acceptance_locks_room_before_membership_capacity_check(monkeypatch):
    host, invitee, circle, invite = (str(uuid.uuid4()) for _ in range(4))
    monkeypatch.setattr(link_circles, "_guard_link", lambda *_args: None)

    def handler(query, params):
        if query.startswith("SELECT circle_id FROM link_circle_invites"):
            return _Result(row=(circle,))
        if query.startswith("SELECT id FROM link_circles") and "FOR UPDATE" in query:
            return _Result(row=(circle,))
        if query.startswith("SELECT i.circle_id,i.inviter_id,c.status"):
            assert "FOR UPDATE OF i" in query
            return _Result(row=(circle, host, "active"))
        if query.startswith("SELECT COUNT(*) FROM link_circle_members"):
            return _Result(row=(31,))
        if query.startswith("SELECT 1 FROM link_circle_members"):
            return _Result(row=None)
        if query.startswith("INSERT INTO link_circle_members"):
            return _Result()
        if query.startswith("UPDATE link_circle_invites"):
            return _Result(row=(invite,))
        raise AssertionError(query)

    connection = _Connection(handler)
    monkeypatch.setattr(link_circles.postgres_db, "connect", lambda *a, **k: _Context(connection))
    assert link_circles.respond_invite(invitee, invite, "accepted") is True
    queries = [query for query, _ in connection.calls]
    lock_index = next(i for i, query in enumerate(queries) if query.startswith("SELECT id FROM link_circles"))
    count_index = next(i for i, query in enumerate(queries) if query.startswith("SELECT COUNT(*)"))
    assert lock_index < count_index
    assert connection.committed is True


def test_invite_recheck_after_room_lock_rejects_already_processed_invite(monkeypatch):
    invitee, circle, invite = (str(uuid.uuid4()) for _ in range(3))

    def handler(query, params):
        if query.startswith("SELECT circle_id FROM link_circle_invites"):
            return _Result(row=(circle,))
        if query.startswith("SELECT id FROM link_circles"):
            return _Result(row=(circle,))
        if query.startswith("SELECT i.circle_id,i.inviter_id,c.status"):
            return _Result(row=None)
        raise AssertionError(query)

    connection = _Connection(handler)
    monkeypatch.setattr(link_circles.postgres_db, "connect", lambda *a, **k: _Context(connection))
    assert link_circles.respond_invite(invitee, invite, "accepted") is False
    assert not any(query.startswith("INSERT INTO link_circle_members") for query, _ in connection.calls)


def test_circle_message_rejects_nonmember_without_writing(monkeypatch):
    author, circle = str(uuid.uuid4()), str(uuid.uuid4())

    def handler(query, params):
        if query.startswith("SELECT id FROM link_circles"):
            return _Result(row=(circle,))
        if query.startswith("SELECT 1 FROM link_circle_members"):
            return _Result(row=None)
        raise AssertionError("Unexpected query: " + query)

    connection = _Connection(handler)
    monkeypatch.setattr(link_circles.postgres_db, "connect", lambda *a, **k: _Context(connection))
    with pytest.raises(ValueError, match="circle_membership_required"):
        link_circles.send_circle_message(author, circle, "secret")
    assert not connection.committed
    assert not any(q.startswith("INSERT") for q, _ in connection.calls)


def test_circle_message_member_write_and_private_read(monkeypatch):
    author, circle, message_id = (str(uuid.uuid4()) for _ in range(3))
    now = datetime.now(UTC)

    def handler(query, params):
        if query.startswith("SELECT id FROM link_circles"):
            return _Result(row=(circle,))
        if query.startswith("SELECT 1 FROM link_circle_members"):
            return _Result(row=(1,))
        if query.startswith("SELECT COUNT(*) FROM link_circle_messages"):
            return _Result(row=(0,))
        if query.startswith("INSERT INTO link_circle_messages"):
            assert params == (circle, author, "Hello Room")
            return _Result(row=(message_id,))
        if query.startswith("SELECT id,sender_id,body,created_at"):
            assert params == (circle, 50)
            return _Result(rows=[(message_id, author, "Hello Room", now)])
        raise AssertionError(query)

    connection = _Connection(handler)
    monkeypatch.setattr(link_circles.postgres_db, "connect", lambda *a, **k: _Context(connection))
    assert link_circles.send_circle_message(author, circle, "Hello Room") == message_id
    assert connection.committed
    assert link_circles.circle_messages(author, circle) == [
        {"message_id": message_id, "sender_id": author,
         "body": "Hello Room", "created_at": now.isoformat()}
    ]


def test_circle_message_routes_require_authentication_and_csrf(anonymous_client, client):
    circle = str(uuid.uuid4())
    path = f"/linkup/circles/{circle}/messages"
    assert anonymous_client.get(path).status_code == 401
    assert anonymous_client.post(path, json={"body": "hello"}).status_code == 401
    assert client.post(path, json={"body": "hello"}).status_code == 403


def test_circle_message_route_unready_never_reads_messages(client, monkeypatch):
    monkeypatch.setattr(link_circles, "status", lambda: {"ready": False})
    response = client.get(f"/linkup/circles/{uuid.uuid4()}/messages")
    assert response.status_code == 503


def test_circle_message_route_requires_message_table_not_just_membership(client, monkeypatch):
    monkeypatch.setattr(link_circles, "status", lambda: {
        "ready": True, "messages_ready": False,
    })
    path = f"/linkup/circles/{uuid.uuid4()}/messages"
    assert client.get(path).status_code == 503
    response = client.get("/linkup/circles/status")
    assert response.status_code == 200
    assert response.get_json()["circle_messages_ready"] is False
