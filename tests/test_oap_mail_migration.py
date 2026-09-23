"""Bounded Mail migration tests: all database operations use fakes."""
from __future__ import annotations

from contextlib import contextmanager

import pytest

from mission_control import mail_migration, mail_preflight, postgres_db


class Connection:
    def __init__(self, version=None, fail_schema=False, invalid_structure=None):
        self.version = version
        self.fail_schema = fail_schema
        self.invalid_structure = invalid_structure
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
        if "SELECT indexdef FROM pg_indexes" in sql:
            if self.invalid_structure == "index":
                return ("CREATE INDEX idx_oap_mail_owner_folder_created "
                        "ON oap_mail_items (subject)",)
            return ("CREATE INDEX idx_oap_mail_owner_folder_created "
                    "ON oap_mail_items (owner_id, folder, created_at DESC)",)
        return (1,)

    def fetchall(self):
        sql = self.commands[-1][0]
        if "FROM information_schema.columns" in sql:
            columns = [
                ("id", "uuid", "NO"), ("owner_id", "uuid", "NO"),
                ("folder", "text", "NO"), ("subject", "text", "NO"),
                ("body", "text", "NO"), ("correspondent", "text", "NO"),
                ("created_at", "timestamp with time zone", "NO"),
                ("updated_at", "timestamp with time zone", "NO"),
            ]
            if self.invalid_structure == "columns":
                columns = [row for row in columns if row[0] != "owner_id"]
            return columns
        if "FROM pg_constraint" in sql:
            if self.invalid_structure == "owner_fk":
                return [("FOREIGN KEY (owner_id) REFERENCES other(id)",)]
            return [("FOREIGN KEY (owner_id) REFERENCES users(id) "
                     "ON DELETE CASCADE",)]
        raise AssertionError("unexpected read-only catalogue query")

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
    # The fake recovery attestation is test-only, never operator proof.
    monkeypatch.setattr(mail_preflight, "report", lambda: {
        "database_configured": True,
        "database_reachable": True,
        "base_schema_ready": True,
        "target_mapping_proven": True,
        "recovery_point_verified": True,
        "independent_release_evidence_verified": True,
        "live_migration_authorized": True,
        "database_authority": "primary",
        "database_source": "primary_override",
    })
    monkeypatch.setattr(postgres_db, "database_authority", lambda: "primary")
    monkeypatch.setattr(postgres_db, "database_source", lambda: "primary_override")


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


def test_mail_migration_refuses_yes_without_independent_proof(monkeypatch):
    """A --yes flag and reachable base DB must never cause any write."""
    operations = []
    monkeypatch.setattr(mail_preflight, "report", lambda: {
        "target_mapping_proven": False,
        "recovery_point_verified": False,
        "independent_release_evidence_verified": False,
        "live_migration_authorized": False,
    })
    monkeypatch.setattr(postgres_db, "postgres_status",
                        lambda: operations.append("status"))
    monkeypatch.setattr(postgres_db, "connect",
                        lambda **_kw: operations.append("connect"))
    with pytest.raises(RuntimeError, match="mail_independent_recovery_evidence_required"):
        mail_migration.init_schema(assume_yes=True)
    assert operations == []


def test_mail_migration_rejects_target_switch_before_connection(monkeypatch):
    operations = []
    monkeypatch.setattr(mail_preflight, "report", lambda: {
        "database_configured": True,
        "database_reachable": True,
        "base_schema_ready": True,
        "target_mapping_proven": True,
        "recovery_point_verified": True,
        "independent_release_evidence_verified": True,
        "live_migration_authorized": True,
        "database_authority": "primary",
        "database_source": "primary_override",
    })
    monkeypatch.setattr(postgres_db, "database_authority", lambda: "primary")
    monkeypatch.setattr(postgres_db, "database_source",
                        lambda: "fallback_override")
    monkeypatch.setattr(postgres_db, "postgres_status",
                        lambda: operations.append("status"))
    monkeypatch.setattr(postgres_db, "connect",
                        lambda **_kw: operations.append("connect"))
    with pytest.raises(RuntimeError, match="mail_database_target_changed"):
        mail_migration.init_schema(assume_yes=True)
    assert operations == []


@pytest.mark.parametrize("invalid,missing", [
    ("columns", "columns_ready"),
    ("index", "index_shape_ready"),
    ("owner_fk", "owner_fk_ready"),
])
def test_mail_schema_rejects_matching_names_with_wrong_shape(
    monkeypatch, invalid, missing,
):
    checksum = mail_migration._checksum(mail_migration._statements())
    connection = Connection(version=checksum, invalid_structure=invalid)
    attach(monkeypatch, connection)
    result = mail_migration.schema_status()
    assert result["table_ready"] is True
    assert result["index_ready"] is True
    assert result[missing] is False
    assert result["schema_ready"] is False
    assert result["error"] == "mail_schema_structure_mismatch"
    assert not connection.committed
