from __future__ import annotations

import json
import uuid
from contextlib import contextmanager
from datetime import UTC, datetime

from mission_control import pulse_routes, pulse_store

POST_ID = "22222222-2222-4222-8222-222222222222"


class _Result:
    def __init__(self, row=None, rows=None):
        self._row = row
        self._rows = list(rows or [])

    def fetchone(self):
        return self._row

    def fetchall(self):
        return self._rows


class _WriteConnection:
    def __init__(self):
        self.calls = []
        self.committed = False

    def execute(self, sql, parameters=None):
        compact = " ".join(sql.split())
        self.calls.append((compact, parameters))
        if compact.startswith("SELECT COUNT(*) FROM posts"):
            return _Result(row=(0,))
        return _Result()

    def commit(self):
        self.committed = True


def _post_projection(body="Local Pulse"):
    return {
        "id": POST_ID,
        "name": "Mitcham",
        "body": body,
        "created_at": "now",
        "reactions": {reaction: 0 for reaction in pulse_store.ALLOWED_REACTIONS},
        "reaction_total": 0,
        "replies": [],
    }


def test_pulse_store_uses_its_own_posts_scope(monkeypatch):
    connection = _WriteConnection()

    @contextmanager
    def fake_connect(*, readonly=False):
        assert readonly is False
        yield connection

    monkeypatch.setattr(pulse_store.postgres_db, "connect", fake_connect)

    pulse_store.add_post(
        "11111111-1111-4111-8111-111111111111",
        name="Mitcham",
        body="Local Pulse",
    )

    inserts = [call for call in connection.calls if call[0].startswith("INSERT INTO posts")]
    assert len(inserts) == 1
    assert inserts[0][1][2] == pulse_store.PULSE_SCOPE == "oap_pulse"
    assert pulse_store.PULSE_SCOPE != "oap_signal"
    assert connection.committed is True


def test_pulse_store_projects_reactions_and_replies_without_identity_ids(monkeypatch):
    created_at = datetime(2026, 9, 3, 18, 0, tzinfo=UTC)

    class _ReadConnection:
        def execute(self, sql, parameters=None):
            compact = " ".join(sql.split())
            if compact.startswith("SELECT id,body,created_at FROM posts"):
                assert parameters == (
                    pulse_store.PULSE_SCOPE,
                    pulse_store.MAX_PULSE_RECORDS,
                )
                return _Result(
                    rows=[
                        (
                            POST_ID,
                            '{"name":"Mitcham","body":"Local Pulse"}',
                            created_at,
                        )
                    ]
                )
            if compact.startswith("SELECT scope,body,created_at FROM posts"):
                return _Result(
                    rows=[
                        (
                            pulse_store.PULSE_REPLY_SCOPE,
                            json.dumps(
                                {
                                    "target_id": POST_ID,
                                    "name": "CR4",
                                    "body": "Reply",
                                }
                            ),
                            created_at,
                        ),
                        (
                            pulse_store.PULSE_REACTION_SCOPE,
                            json.dumps(
                                {"target_id": POST_ID, "reaction": "like"}
                            ),
                            created_at,
                        ),
                    ]
                )
            raise AssertionError(compact)

    @contextmanager
    def fake_connect(*, readonly=False):
        assert readonly is True
        yield _ReadConnection()

    monkeypatch.setattr(pulse_store.postgres_db, "connect", fake_connect)

    result = pulse_store.list_posts()

    assert result[0]["id"] == POST_ID
    assert result[0]["reactions"]["like"] == 1
    assert result[0]["reaction_total"] == 1
    assert result[0]["replies"][0]["name"] == "CR4"
    assert result[0]["replies"][0]["body"] == "Reply"
    assert "identity_id" not in result[0]
    assert "identity_id" not in result[0]["replies"][0]


def test_same_reaction_toggles_off(monkeypatch):
    identity = "11111111-1111-4111-8111-111111111111"
    reaction_id = "33333333-3333-4333-8333-333333333333"

    class _ReactionConnection(_WriteConnection):
        def execute(self, sql, parameters=None):
            compact = " ".join(sql.split())
            self.calls.append((compact, parameters))
            if compact.startswith("SELECT COUNT(*) FROM posts"):
                return _Result(row=(0,))
            if compact.startswith("SELECT 1 FROM posts"):
                return _Result(row=(1,))
            if compact.startswith("SELECT id,body FROM posts"):
                return _Result(
                    rows=[
                        (
                            reaction_id,
                            json.dumps(
                                {"target_id": POST_ID, "reaction": "like"}
                            ),
                        )
                    ]
                )
            return _Result()

    connection = _ReactionConnection()

    @contextmanager
    def fake_connect(*, readonly=False):
        assert readonly is False
        yield connection

    monkeypatch.setattr(pulse_store.postgres_db, "connect", fake_connect)

    assert pulse_store.add_reaction(identity, POST_ID, "like") == "removed"
    assert any(call[0].startswith("DELETE FROM posts WHERE id=") for call in connection.calls)
    assert connection.committed is True


def test_pulse_page_is_public_simple_and_separate_from_signal(
    anonymous_client, monkeypatch
):
    monkeypatch.setattr(
        pulse_routes.pulse_store,
        "list_posts",
        lambda: [_post_projection()],
    )

    response = anonymous_client.get("/pulse")
    page = response.get_data(as_text=True)

    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    assert "📡 Pulse" in page
    assert "Local Pulse" in page
    assert 'action="/pulse"' in page
    assert 'action="/signal"' not in page
    assert "👍 Like" in page
    assert "Replies" in page
    assert "Signal feed" not in page


def test_legacy_spot_pulse_uses_same_separate_feed(anonymous_client, monkeypatch):
    monkeypatch.setattr(
        pulse_routes.pulse_store,
        "list_posts",
        lambda: [_post_projection("Spot Pulse")],
    )

    response = anonymous_client.get("/the-spot/pulse")
    page = response.get_data(as_text=True)

    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    assert "📡 Pulse" in page
    assert "Spot Pulse" in page
    assert 'action="/signal"' not in page


def test_pulse_post_is_csrf_guarded(client, monkeypatch):
    called = []
    monkeypatch.setattr(
        pulse_routes.pulse_store,
        "add_post",
        lambda *args, **kwargs: called.append((args, kwargs)),
    )

    response = client.post("/pulse", data={"name": "Mitcham", "body": "Hello"})

    assert response.status_code == 403
    assert response.get_json()["error"]["code"] == "csrf_failed"
    assert called == []


def test_pulse_post_lands_under_public_session_identity(client, csrf, monkeypatch):
    observed = {}

    def fake_add(identity_id, *, name, body):
        observed.update(identity_id=identity_id, name=name, body=body)

    monkeypatch.setattr(pulse_routes.pulse_store, "add_post", fake_add)

    response = client.post(
        "/pulse",
        data={**csrf, "name": "Mitcham", "body": "What’s happening"},
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/pulse")
    assert observed["name"] == "Mitcham"
    assert observed["body"] == "What’s happening"
    assert observed["identity_id"] != "11111111-1111-4111-8111-111111111111"
    uuid.UUID(observed["identity_id"])


def test_reaction_route_uses_public_session_identity(client, csrf, monkeypatch):
    observed = {}

    def fake_reaction(identity_id, post_id, reaction):
        observed.update(identity_id=identity_id, post_id=post_id, reaction=reaction)
        return "set"

    monkeypatch.setattr(pulse_routes.pulse_store, "add_reaction", fake_reaction)

    response = client.post(
        f"/pulse/{POST_ID}/reaction",
        data={**csrf, "reaction": "like"},
    )

    assert response.status_code == 302
    assert observed["post_id"] == POST_ID
    assert observed["reaction"] == "like"
    assert observed["identity_id"] != "11111111-1111-4111-8111-111111111111"
    uuid.UUID(observed["identity_id"])


def test_reply_route_is_csrf_guarded_and_bounded_by_store(client, csrf, monkeypatch):
    observed = {}

    def fake_reply(identity_id, post_id, *, name, body):
        observed.update(identity_id=identity_id, post_id=post_id, name=name, body=body)

    monkeypatch.setattr(pulse_routes.pulse_store, "add_reply", fake_reply)

    response = client.post(
        f"/pulse/{POST_ID}/reply",
        data={**csrf, "name": "CR4", "body": "Local reply"},
    )

    assert response.status_code == 302
    assert observed["post_id"] == POST_ID
    assert observed["name"] == "CR4"
    assert observed["body"] == "Local reply"

    missing_csrf = client.post(
        f"/pulse/{POST_ID}/reply",
        data={"name": "CR4", "body": "Blocked"},
    )
    assert missing_csrf.status_code == 403
