"""Opaque database target fingerprint: read-only, stable and secret-free."""
from __future__ import annotations

from contextlib import contextmanager

from mission_control import postgres_db


class _Result:
    def __init__(self, value, metadata_value="fedcba9876543210fedcba9876543210"):
        self.value = value
        self.metadata_value = metadata_value

    def fetchone(self):
        return (self.value, self.metadata_value)


class _Connection:
    def __init__(self):
        self.queries = []

    def execute(self, sql):
        self.queries.append(sql)
        return _Result("0123456789abcdef0123456789abcdef")


def test_database_identity_fingerprint_is_readonly_and_opaque(monkeypatch):
    connection = _Connection()
    opens = []

    @contextmanager
    def fake_connect(*, readonly=False):
        opens.append(readonly)
        yield connection

    monkeypatch.setattr(postgres_db, "configured", lambda: True)
    monkeypatch.setattr(postgres_db, "database_source",
                        lambda: "platform_database_url")
    monkeypatch.setattr(postgres_db, "database_authority", lambda: "primary")
    monkeypatch.setattr(postgres_db, "connect", fake_connect)

    result = postgres_db.database_identity_fingerprint()

    assert result == {
        "source": "platform_database_url",
        "authority": "primary",
        "fingerprint": "0123456789abcdef0123456789abcdef",
        "metadata_fingerprint": "fedcba9876543210fedcba9876543210",
        "metadata_fingerprint_algorithm": "md5",
        "metadata_fingerprint_components": ["current_database", "current_user"],
        "reachable": True,
        "secret_exposed": False,
        "error": None,
    }
    assert opens == [True]
    assert len(connection.queries) == 1
    sql = connection.queries[0].lower()
    assert "md5(" in sql
    assert "current_database()" in sql
    assert "inet_server_addr()" in sql
    assert "current_user" in sql
    assert "password" not in sql
    assert "database_url" not in sql


def test_database_identity_fingerprint_fails_closed_without_configuration(monkeypatch):
    monkeypatch.setattr(postgres_db, "configured", lambda: False)
    monkeypatch.setattr(postgres_db, "database_source", lambda: "unconfigured")
    monkeypatch.setattr(postgres_db, "database_authority", lambda: "primary")
    monkeypatch.setattr(
        postgres_db, "connect",
        lambda **_kwargs: (_ for _ in ()).throw(
            AssertionError("unconfigured fingerprint must not connect")
        ),
    )

    result = postgres_db.database_identity_fingerprint()

    assert result["fingerprint"] is None
    assert result["reachable"] is False
    assert result["error"] == "database_url_not_configured"
    assert result["secret_exposed"] is False


def test_database_identity_fingerprint_rejects_malformed_database_value(monkeypatch):
    connection = _Connection()
    connection.execute = lambda _sql: _Result("not-a-fingerprint")

    @contextmanager
    def fake_connect(*, readonly=False):
        assert readonly is True
        yield connection

    monkeypatch.setattr(postgres_db, "configured", lambda: True)
    monkeypatch.setattr(postgres_db, "database_source",
                        lambda: "platform_database_url")
    monkeypatch.setattr(postgres_db, "database_authority", lambda: "primary")
    monkeypatch.setattr(postgres_db, "connect", fake_connect)

    result = postgres_db.database_identity_fingerprint()

    assert result["fingerprint"] is None
    assert result["reachable"] is False
    assert result["error"] == "database_identity_unavailable"



def test_database_identity_fingerprint_rejects_malformed_metadata_value(monkeypatch):
    connection = _Connection()
    connection.execute = lambda _sql: _Result(
        "0123456789abcdef0123456789abcdef", "not-a-fingerprint",
    )

    @contextmanager
    def fake_connect(*, readonly=False):
        assert readonly is True
        yield connection

    monkeypatch.setattr(postgres_db, "configured", lambda: True)
    monkeypatch.setattr(postgres_db, "database_source",
                        lambda: "platform_database_url")
    monkeypatch.setattr(postgres_db, "database_authority", lambda: "primary")
    monkeypatch.setattr(postgres_db, "connect", fake_connect)

    result = postgres_db.database_identity_fingerprint()

    assert result["fingerprint"] is None
    assert result["metadata_fingerprint"] is None
    assert result["reachable"] is False
    assert result["error"] == "database_identity_unavailable"
