from __future__ import annotations

import uuid

import pytest

from mission_control import link_presence, link_presence_routes


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


def _allow_link(monkeypatch):
    monkeypatch.setattr(
        link_presence.linkup_safety, "blocked_between", lambda _first, _second: False
    )
    monkeypatch.setattr(
        link_presence.link_relationships, "accepted_between", lambda _first, _second: True
    )


def test_presence_schema_is_explicit_first_party_and_bounded():
    dry_run = link_presence.init_schema(dry_run=True)
    joined = "\n".join(dry_run["statements"])

    assert dry_run["version"] == "link_presence_v1"
    assert dry_run["applied"] is False
    assert "link_presence_state" in joined
    assert "link_presence_visibility" in joined
    assert "link_live_spot" in joined
    assert "latitude BETWEEN -90 AND 90" in joined
    assert "longitude BETWEEN -180 AND 180" in joined
    assert "around_now BOOLEAN NOT NULL DEFAULT FALSE" in joined
    assert "live_spot BOOLEAN NOT NULL DEFAULT FALSE" in joined
    assert link_presence.PRESENCE_TTL_SECONDS == 120
    assert link_presence.MAX_LIVE_SPOT_MINUTES == 60


def test_presence_block_guard_runs_before_store(monkeypatch):
    monkeypatch.setattr(
        link_presence.linkup_safety, "blocked_between", lambda _first, _second: True
    )
    monkeypatch.setattr(
        link_presence.postgres_db,
        "connect",
        lambda *args, **kwargs: pytest.fail("presence store must not be reached"),
    )

    with pytest.raises(ValueError, match="link_blocked"):
        link_presence.set_visibility(uuid.uuid4(), uuid.uuid4(), around_now=True)


def test_presence_requires_accepted_link_before_store(monkeypatch):
    monkeypatch.setattr(
        link_presence.linkup_safety, "blocked_between", lambda _first, _second: False
    )
    monkeypatch.setattr(
        link_presence.link_relationships, "accepted_between", lambda _first, _second: False
    )
    monkeypatch.setattr(
        link_presence.postgres_db,
        "connect",
        lambda *args, **kwargs: pytest.fail("presence store must not be reached"),
    )

    with pytest.raises(ValueError, match="accepted_link_required"):
        link_presence.set_visibility(uuid.uuid4(), uuid.uuid4(), live_spot=True)


def test_visibility_defaults_private_and_disabling_live_spot_deletes_share(monkeypatch):
    _allow_link(monkeypatch)

    def handler(query, _params):
        if query.startswith("INSERT INTO link_presence_visibility"):
            return _Result()
        if query.startswith("DELETE FROM link_live_spot"):
            return _Result(rowcount=1)
        raise AssertionError(f"unexpected query: {query}")

    connection = _Connection(handler)
    monkeypatch.setattr(
        link_presence.postgres_db, "connect", lambda *args, **kwargs: _Context(connection)
    )

    result = link_presence.set_visibility(
        uuid.uuid4(), uuid.uuid4(), around_now=False, live_spot=False
    )

    assert result == {"around_now": False, "live_spot": False}
    assert any(query.startswith("DELETE FROM link_live_spot") for query, _ in connection.calls)
    assert connection.committed is True


def test_around_now_read_requires_visibility_and_unexpired_heartbeat(monkeypatch):
    _allow_link(monkeypatch)
    connection = _Connection(lambda _query, _params: _Result(row=(1,)))
    monkeypatch.setattr(
        link_presence.postgres_db, "connect", lambda *args, **kwargs: _Context(connection)
    )

    assert link_presence.around_now(uuid.uuid4(), uuid.uuid4()) is True
    query = connection.calls[0][0]
    assert "v.around_now=TRUE" in query
    assert "s.around_now=TRUE" in query
    assert "s.expires_at>CURRENT_TIMESTAMP" in query


def test_live_spot_requires_explicit_visibility_and_bounded_duration(monkeypatch):
    _allow_link(monkeypatch)
    owner = uuid.uuid4()
    viewer = uuid.uuid4()

    with pytest.raises(ValueError, match="invalid_live_spot_coordinates"):
        link_presence.start_live_spot(
            owner, viewer, latitude=91, longitude=0, duration_minutes=15
        )

    with pytest.raises(ValueError, match="invalid_live_spot_duration"):
        link_presence.start_live_spot(
            owner, viewer, latitude=51.4, longitude=-0.16, duration_minutes=61
        )

    connection = _Connection(
        lambda query, _params: _Result(row=None)
        if query.startswith("SELECT 1 FROM link_presence_visibility")
        else pytest.fail(f"unexpected query: {query}")
    )
    monkeypatch.setattr(
        link_presence.postgres_db, "connect", lambda *args, **kwargs: _Context(connection)
    )

    with pytest.raises(ValueError, match="live_spot_visibility_required"):
        link_presence.start_live_spot(
            owner, viewer, latitude=51.4, longitude=-0.16, duration_minutes=15
        )


def test_live_spot_stop_is_immediate_and_does_not_require_link_guard(monkeypatch):
    owner = str(uuid.uuid4())
    viewer = str(uuid.uuid4())
    connection = _Connection(lambda _query, _params: _Result(row=(owner,)))
    monkeypatch.setattr(
        link_presence.postgres_db, "connect", lambda *args, **kwargs: _Context(connection)
    )
    monkeypatch.setattr(
        link_presence.linkup_safety,
        "blocked_between",
        lambda *_args: pytest.fail("stop must remain available even after Block"),
    )

    assert link_presence.stop_live_spot(owner, viewer) is True
    assert connection.calls[0][0].startswith("DELETE FROM link_live_spot")
    assert connection.committed is True


def test_presence_status_route_rejects_anonymous_access(anonymous_client):
    response = anonymous_client.get("/linkup/presence/status")

    assert response.status_code == 401
    assert response.get_json()["error"]["code"] == "authentication_required"


def test_presence_status_route_is_coarse_and_no_store(client, monkeypatch):
    monkeypatch.setattr(
        link_presence_routes.link_presence,
        "status",
        lambda: {
            "configured": True,
            "schema_ready": True,
            "ready": True,
            "private_by_default": True,
            "first_party": True,
        },
    )

    response = client.get("/linkup/presence/status")

    assert response.status_code == 200
    assert response.get_json()["first_party"] is True
    assert response.get_json()["private_by_default"] is True
    assert response.headers["Cache-Control"] == "no-store"


def test_presence_mutations_require_csrf(client):
    peer = str(uuid.uuid4())
    visibility = client.post(
        "/linkup/presence/visibility",
        json={"peer_id": peer, "around_now": True, "live_spot": False},
    )
    spot = client.post(
        "/linkup/live-spot",
        json={
            "peer_id": peer,
            "latitude": 51.4,
            "longitude": -0.16,
            "duration_minutes": 15,
        },
    )

    assert visibility.status_code == 403
    assert visibility.get_json()["error"]["code"] == "csrf_failed"
    assert spot.status_code == 403
    assert spot.get_json()["error"]["code"] == "csrf_failed"
