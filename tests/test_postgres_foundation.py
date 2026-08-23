"""Fail-closed checks for the optional Render PostgreSQL foundation."""

from mission_control import config, db


def test_postgres_status_redacts_connection_url(monkeypatch):
    monkeypatch.setattr(config, "DATABASE_BACKEND", "postgresql")
    monkeypatch.setattr(
        config,
        "DATABASE_URL",
        "postgresql://private-user:private-password@db.internal/oap",
    )

    def unavailable(*, readonly=False):
        assert readonly is True
        raise RuntimeError("database unavailable")

    monkeypatch.setattr(db, "_connect", unavailable)
    status = db.db_status()

    assert status["backend"] == "postgresql"
    assert status["db_path"] is None
    assert status["exists"] is False
    assert status["initialized"] is False
    assert status["error"] == "database_unavailable"
    assert "private-password" not in repr(status)


def test_sqlite_remains_the_local_first_test_backend():
    assert config.DATABASE_BACKEND == "sqlite"
