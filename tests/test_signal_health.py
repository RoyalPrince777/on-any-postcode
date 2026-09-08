from __future__ import annotations

from contextlib import contextmanager

from mission_control import signal_health

POST_ID = "22222222-2222-4222-8222-222222222222"


class _Result:
    def __init__(self, row=None):
        self._row = row

    def fetchone(self):
        return self._row


class _WriteConnection:
    def __init__(self):
        self.rollback_called = False
        self.inserted_payload = ""

    def execute(self, sql, parameters=None):
        compact = " ".join(sql.split())
        if compact.startswith("INSERT INTO posts"):
            self.inserted_payload = str(parameters[1])
            return _Result(row=(POST_ID,))
        if compact.startswith("SELECT body FROM posts"):
            return _Result(row=(self.inserted_payload,))
        return _Result()

    def rollback(self):
        self.rollback_called = True


class _ReadConnection:
    def execute(self, sql, parameters=None):
        compact = " ".join(sql.split())
        assert compact.startswith("SELECT EXISTS(SELECT 1 FROM users")
        assert parameters[1] == POST_ID
        return _Result(row=(False,))


def test_signal_roundtrip_proof_rolls_back_and_checks_residue(monkeypatch):
    write_connection = _WriteConnection()
    read_connection = _ReadConnection()
    calls = []

    monkeypatch.setattr(signal_health.postgres_db, "configured", lambda: True)

    @contextmanager
    def fake_connect(*, readonly=False):
        calls.append(readonly)
        yield read_connection if readonly else write_connection

    monkeypatch.setattr(signal_health.postgres_db, "connect", fake_connect)
    signal_health._probe_cache = None

    assert signal_health._roundtrip_probe(force=True) is True
    assert write_connection.rollback_called is True
    assert calls == [False, True]
    assert "oap-signal-probe-" in write_connection.inserted_payload


def test_signal_health_endpoint_reports_ready_without_caching(anonymous_client, monkeypatch):
    monkeypatch.setattr(signal_health, "_roundtrip_probe", lambda: True)

    response = anonymous_client.get("/signal/health")

    assert response.status_code == 200
    assert response.get_json() == {"status": "healthy"}
    assert response.headers["Cache-Control"] == "no-store"


def test_signal_health_endpoint_fails_closed(anonymous_client, monkeypatch):
    monkeypatch.setattr(signal_health, "_roundtrip_probe", lambda: False)

    response = anonymous_client.get("/signal/health")

    assert response.status_code == 503
    assert response.get_json() == {"status": "unavailable"}
