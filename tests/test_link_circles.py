from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest

from mission_control import link_circle_routes, link_circles


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
    assert "status IN ('active','closed')" in joined
    assert "role IN ('host','member')" in joined
    assert "status IN ('pending','accepted','declined','revoked')" in joined
    assert link_circles.MAX_CIRCLE_MEMBERS == 32
    assert "message" not in joined.casefold()
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

    monkeypatch.setattr(link_circles.linkup_safety, "blocked_between", lambda *_args: False)
    monkeypatch.setattr(link_circles.link_relationships, "accepted_between", lambda *_args: False)
    with pytest.raises(ValueError, match="accepted_link_required"):
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
            assert params == (successor_membership,)
            return _Result()
        if query.startswith("UPDATE link_circles SET host_id="):
            assert params == (successor, circle)
            return _Result()
        if query.startswith("UPDATE link_circle_members SET status='left'"):
            assert params == (host_membership,)
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
            assert params == (circle,)
            return _Result()
        if query.startswith("UPDATE link_circle_invites SET status='revoked'"):
            assert params == (circle,)
            return _Result()
        if query.startswith("UPDATE link_circle_members SET status='left'"):
            assert params == (membership,)
            return _Result()
        raise AssertionError(query)

    connection = _Connection(handler)
    monkeypatch.setattr(link_circles.postgres_db, "connect", lambda *a, **k: _Context(connection))
    assert link_circles.step_out(host, circle) is True
    assert connection.committed is True


def test_circle_dashboard_never_returns_message_or_media_content(monkeypatch):
    identity = str(uuid.uuid4())
    circle = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    calls = 0

    def handler(query, params):
        nonlocal calls
        calls += 1
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
    assert data["circles"][0]["members"][0]["role"] == "host"
    assert calls == 3


def test_circle_status_requires_auth_and_is_fail_closed(anonymous_client, client, monkeypatch):
    anonymous = anonymous_client.get("/linkup/circles/status")
    assert anonymous.status_code == 401

    monkeypatch.setattr(link_circle_routes.link_circles, "status", lambda: {"ready": False})
    response = client.get("/linkup/circles/status")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["ready"] is False
    assert payload["circle_messages_ready"] is False
    assert payload["circle_calls_ready"] is False
    assert response.headers["Cache-Control"] == "no-store"


def test_circle_page_renders_governed_controls_when_ready(client, monkeypatch):
    monkeypatch.setattr(link_circle_routes.link_circles, "status", lambda: {"ready": True})
    monkeypatch.setattr(
        link_circle_routes.link_circles,
        "dashboard",
        lambda _identity: {"circles": [], "invites": [], "max_members": 32},
    )
    monkeypatch.setattr(link_circle_routes, "_accepted_people", lambda _identity: [])
    response = client.get("/linkup/circles")
    assert response.status_code == 200
    text = response.get_data(as_text=True)
    assert "Start a Circle" in text
    assert "Bring In" in text
    assert "Link In" in text or "No pending Circle invitations" in text
    assert "Step Out" in text or "No Circles yet" in text
    assert "Circle messages, Voice, Call and Face Up remain locked" in text
    assert response.headers["Cache-Control"] == "no-store"


def test_circle_mutation_requires_csrf(client, monkeypatch):
    monkeypatch.setattr(
        link_circle_routes.link_circles,
        "create_circle",
        lambda *_args: pytest.fail("Circle mutation must not run without CSRF"),
    )
    response = client.post("/linkup/circles", data={"name": "Family"})
    assert response.status_code == 403
    assert response.get_json()["error"]["code"] == "csrf_failed"
