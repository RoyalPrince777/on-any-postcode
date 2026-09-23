"""Bounded Mail migration tests: all database operations use fakes."""
from __future__ import annotations

from contextlib import contextmanager

import pytest

from mission_control import mail_migration, postgres_db


class Connection:
    def __init__(self, version=None, fail_schema=False):
        self.version = version
        self.fail_schema = fail_schema
        self.commands = []
        self.committed = False
        self.rolled_back = False

    def execute(self, sql, params=None):
        self.commands.append((sql, params))
        if sql.startswith("INSERT INTO oap_schema_migrations"):
            self.version = params[1]
        if self.fail_schema and sql.startswith("CREATE TABLE"):
            raise RuntimeError("forced_migration_failure")
        return self

    def fetchone(self):
        sql = self.commands[-1][0]
        if "SELECT checksum FROM oap_schema_migrations" in sql:
            return (self.version,) if self.version is not None else None
        return (1,)

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True


def attach(monkeypatch, connection):
    @contextmanager
    def connect(*, readonly=False):
        yield connection
    monkeypatch.setattr(postgres_db, "connect", connect)
    monkeypatch.setattr(postgres_db, "postgres_status",
                        lambda: {"initialized": True})


def test_mail_requires_explicit_approval_and_dry_run_never_connects(monkeypatch):
    def forbidden(*, readonly=False):
        raise AssertionError("unexpected database connection")
    monkeypatch.setattr(postgres_db, "connect", forbidden)
    with pytest.raises(RuntimeError, match="Explicit human approval"):
        mail_migration.init_schema(dry_run=True)
    result = mail_migration.init_schema(dry_run=True, assume_yes=True)
    assert result["applied"] is False
    assert result["statements"] == 2
    assert len(result["checksum"]) == 64


def test_mail_checksum_mismatch_rolls_back_before_ddl(monkeypatch):
    connection = Connection(version="invalid-checksum")
    attach(monkeypatch, connection)
    with pytest.raises(RuntimeError, match="mail_migration_checksum_mismatch"):
        mail_migration.init_schema(assume_yes=True)
    assert connection.rolled_back is True
    assert connection.committed is False
    assert not any(sql.startswith("CREATE TABLE") for sql, _ in connection.commands)


def test_mail_new_migration_commits_and_repeats_without_ddl(monkeypatch):
    connection = Connection()
    attach(monkeypatch, connection)
    result = mail_migration.init_schema(assume_yes=True)
    assert result["schema_ready"] is True
    assert connection.committed is True
    assert sum(sql.startswith("CREATE TABLE") for sql, _ in connection.commands) == 1
    second = Connection(version=result["checksum"])
    attach(monkeypatch, second)
    mail_migration.init_schema(assume_yes=True)
    assert not any(sql.startswith("CREATE TABLE") for sql, _ in second.commands)


def test_mail_migration_failure_rolls_back(monkeypatch):
    connection = Connection(fail_schema=True)
    attach(monkeypatch, connection)
    with pytest.raises(RuntimeError, match="forced_migration_failure"):
        mail_migration.init_schema(assume_yes=True)
    assert connection.rolled_back is True
    assert connection.committed is False


def test_mail_schema_status_detects_mismatch(monkeypatch):
    connection = Connection(version="invalid-checksum")
    attach(monkeypatch, connection)
    result = mail_migration.schema_status()
    assert result["schema_ready"] is False
    assert result["error"] == "mail_migration_checksum_mismatch"
