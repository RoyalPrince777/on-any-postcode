from __future__ import annotations

from contextlib import contextmanager
from datetime import UTC, datetime

from mission_control import pulse_routes, pulse_store


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


def test_pulse_store_reads_only_pulse_scope(monkeypatch):
    created_at = datetime(2026, 9, 3, 18, 0, tzinfo=UTC)

    class _ReadConnection:
        def execute(self, sql, parameters=None):
            assert "WHERE scope=%s AND status='published'" in sql
            assert parameters == (pulse_store.PULSE_SCOPE, pulse_store.MAX_PULSE_RECORDS)
            return _Result(
                rows=[('{"name":"Mitcham","body":"Local Pulse"}', created_at)]
            )

    @contextmanager
    def fake_connect(*, readonly=False):
        assert readonly is True
        yield _ReadConnection()

    monkeypatch.setattr(pulse_store.postgres_db, "connect", fake_connect)

    assert pulse_store.list_posts() == [
        {
            "name": "Mitcham",
            "body": "Local Pulse",
            "created_at": "2026-09-03 18:00:00+00:00",
        }
    ]


def test_pulse_page_is_public_simple_and_separate_from_signal(anonymous_client, monkeypatch):
    monkeypatch.setattr(
        pulse_routes.pulse_store,
        "list_posts",
        lambda: [
            {
                "name": "Mitcham",
                "body": "Local Pulse",
                "created_at": "now",
            }
        ],
    )

    response = anonymous_client.get("/pulse")
    page = response.get_data(as_text=True)

    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    assert "📡 Pulse" in page
    assert "Local Pulse" in page
    assert 'action="/pulse"' in page
    assert 'action="/signal"' not in page
    assert "Signal feed" not in page


def test_legacy_spot_pulse_uses_same_separate_feed(anonymous_client, monkeypatch):
    monkeypatch.setattr(
        pulse_routes.pulse_store,
        "list_posts",
        lambda: [
            {
                "name": "Mitcham",
                "body": "Spot Pulse",
                "created_at": "now",
            }
        ],
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


def test_pulse_post_lands_in_pulse_store(client, csrf, monkeypatch):
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
    assert observed == {
        "identity_id": "11111111-1111-4111-8111-111111111111",
        "name": "Mitcham",
        "body": "What’s happening",
    }
