from __future__ import annotations

import pytest

from mission_control import database, postgres_db


def test_postgres_is_opt_in_and_redacted(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    status = postgres_db.postgres_status()
    assert status["configured"] is False
    assert status["error"] == "database_url_not_configured"
    assert "url" not in status
    assert database.db_status()["backend"] == "sqlite"


def test_postgres_requires_explicit_human_approval(monkeypatch):
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql://example.invalid/oap?sslmode=require",
    )
    with pytest.raises(RuntimeError, match="Explicit human approval"):
        postgres_db.init_postgres()
    assert postgres_db.postgres_status()["error"] == "database_unavailable"


def test_production_schema_preserves_governance_boundaries():
    schema = "\n".join(postgres_db.MIGRATION_STATEMENTS)
    for table in postgres_db.REQUIRED_TABLES:
        assert table in schema
    assert "APPROVED" in schema
    assert "REJECTED" in schema
    assert "EXECUTE" not in schema
    assert "Kaa" not in schema


def test_database_url_is_never_returned(monkeypatch):
    secret = "postgresql://owner:do-not-expose@example.invalid/oap"
    monkeypatch.setenv("DATABASE_URL", secret)
    assert secret not in repr(postgres_db.postgres_status())
