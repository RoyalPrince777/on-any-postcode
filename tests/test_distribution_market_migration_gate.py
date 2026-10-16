from __future__ import annotations

import pytest

from mission_control import distribution_market_links as links


class Result:
    def __init__(self, one=None):
        self.one = one

    def fetchone(self):
        return self.one


class MigrationConnection:
    def __init__(self, *, migration=None, fail_on_create=False, status_ready=True):
        self.migration = migration
        self.fail_on_create = fail_on_create
        self.status_ready = status_ready
        self.commands = []
        self.commits = 0
        self.rollbacks = 0

    def execute(self, sql, params=None):
        self.commands.append((sql, params))
        if sql.startswith("SELECT pg_advisory_xact_lock"):
            return Result((1,))
        if "SELECT checksum FROM oap_schema_migrations" in sql:
            return Result(self.migration)
        if "FROM information_schema.tables" in sql:
            return Result((1,) if self.status_ready else None)
        if "FROM pg_indexes" in sql:
            return Result((1,) if self.status_ready else None)
        if sql.startswith("CREATE TABLE") and self.fail_on_create:
            raise RuntimeError("ddl_failed")
        if sql.startswith("INSERT INTO oap_schema_migrations"):
            self.migration = (links.LINK_SCHEMA_CHECKSUM,)
        return Result()

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False


def install(monkeypatch, connection):
    monkeypatch.setattr(
        links.postgres_db,
        "connect",
        lambda readonly=False: connection,
    )


def test_production_migration_remains_non_mutating_by_default():
    with pytest.raises(RuntimeError, match="Explicit human approval"):
        links.init_link_schema()
    result = links.init_link_schema(assume_yes=True)
    assert result["dry_run"] is True
    assert result["applied"] is False


def test_migration_uses_advisory_lock_checksum_and_post_apply_readback(monkeypatch):
    connection = MigrationConnection()
    install(monkeypatch, connection)

    result = links.init_link_schema(assume_yes=True, dry_run=False)

    assert result["schema_ready"] is True
    assert result["applied"] is True
    assert connection.commits == 1
    assert connection.rollbacks == 0
    joined = "\n".join(sql for sql, _ in connection.commands)
    assert "pg_advisory_xact_lock" in joined
    assert "SELECT checksum FROM oap_schema_migrations" in joined
    assert "CREATE TABLE IF NOT EXISTS oap_distribution_market_links" in joined
    assert "CREATE INDEX IF NOT EXISTS ix_distribution_market_links_owner_created" in joined


def test_existing_matching_migration_is_idempotent(monkeypatch):
    connection = MigrationConnection(migration=(links.LINK_SCHEMA_CHECKSUM,))
    install(monkeypatch, connection)

    result = links.init_link_schema(assume_yes=True, dry_run=False)

    assert result["schema_ready"] is True
    assert result["applied"] is False
    assert connection.commits == 1
    assert not any(sql.startswith("CREATE TABLE") for sql, _ in connection.commands)


def test_checksum_mismatch_fails_closed_and_rolls_back(monkeypatch):
    connection = MigrationConnection(migration=("0" * 64,))
    install(monkeypatch, connection)

    with pytest.raises(RuntimeError, match="checksum_mismatch"):
        links.init_link_schema(assume_yes=True, dry_run=False)

    assert connection.commits == 0
    assert connection.rollbacks == 1


def test_ddl_failure_rolls_back(monkeypatch):
    connection = MigrationConnection(fail_on_create=True)
    install(monkeypatch, connection)

    with pytest.raises(RuntimeError, match="ddl_failed"):
        links.init_link_schema(assume_yes=True, dry_run=False)

    assert connection.commits == 0
    assert connection.rollbacks == 1


def test_schema_status_redacts_database_errors(monkeypatch):
    def unavailable(*_args, **_kwargs):
        raise RuntimeError("secret database detail")

    monkeypatch.setattr(links.postgres_db, "connect", unavailable)
    status = links.schema_status()

    assert status["schema_ready"] is False
    assert status["error"] == "distribution_market_schema_unavailable"
