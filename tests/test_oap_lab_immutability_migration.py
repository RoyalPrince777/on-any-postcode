"""Explicit migration contract for OAP LAB notebook immutability."""
import pytest

from mission_control import oap_lab_immutability_migration as migration


class _Connection:
    def __init__(self):
        self.sql = []
        self.committed = False

    def execute(self, sql, params=None):
        self.sql.append((sql, params))
        return self

    def commit(self):
        self.committed = True


class _Context:
    def __init__(self, connection):
        self.connection = connection

    def __enter__(self):
        return self.connection

    def __exit__(self, exc_type, exc, tb):
        return False


def test_apply_requires_explicit_human_approval():
    with pytest.raises(
        migration.LabImmutabilityMigrationBlocked,
        match="explicit_human_approval",
    ):
        migration.apply()


def test_apply_uses_only_lab_scoped_update_delete_guard(monkeypatch):
    connection = _Connection()
    states = iter([
        {"database_enforced": False},
        {"database_enforced": True},
    ])
    monkeypatch.setattr(migration.postgres_db, "_lab_database_url", lambda: "postgres://lab")
    monkeypatch.setattr(
        migration.postgres_db, "lab_connect",
        lambda: _Context(connection),
    )
    monkeypatch.setattr(
        migration.workspaces, "lab_immutability_status",
        lambda: next(states),
    )

    result = migration.apply(assume_yes=True)

    assert result["applied"] is True
    assert result["verified"] is True
    assert connection.committed is True
    sql = "\n".join(statement for statement, _ in connection.sql)
    assert "oap_lab_workspace_immutable_guard" in sql
    assert "BEFORE UPDATE OR DELETE ON oap_workspace_records" in sql
    assert "workspace_id = 'governance'" in sql
    assert "title LIKE 'OAP-LAB:%'" in sql
    assert "DROP TABLE" not in sql
    assert "ALTER TABLE" not in sql


def test_apply_failure_does_not_claim_verified(monkeypatch):
    class BrokenConnection(_Connection):
        def execute(self, sql, params=None):
            if "CREATE OR REPLACE FUNCTION" in sql:
                raise RuntimeError("blocked")
            return super().execute(sql, params)

    connection = BrokenConnection()
    monkeypatch.setattr(migration.postgres_db, "_lab_database_url", lambda: "postgres://lab")
    monkeypatch.setattr(
        migration.postgres_db, "lab_connect",
        lambda: _Context(connection),
    )
    monkeypatch.setattr(
        migration.workspaces, "lab_immutability_status",
        lambda: {"database_enforced": False},
    )
    with pytest.raises(
        migration.LabImmutabilityMigrationBlocked,
        match="apply_failed",
    ):
        migration.apply(assume_yes=True)
    assert connection.committed is False


def test_post_apply_probe_must_turn_green(monkeypatch):
    connection = _Connection()
    monkeypatch.setattr(migration.postgres_db, "_lab_database_url", lambda: "postgres://lab")
    monkeypatch.setattr(
        migration.postgres_db, "lab_connect",
        lambda: _Context(connection),
    )
    monkeypatch.setattr(
        migration.workspaces, "lab_immutability_status",
        lambda: {"database_enforced": False},
    )
    with pytest.raises(
        migration.LabImmutabilityMigrationBlocked,
        match="post_apply_proof_failed",
    ):
        migration.apply(assume_yes=True)


def test_existing_database_protection_is_idempotent(monkeypatch):
    monkeypatch.setattr(migration.postgres_db, "_lab_database_url", lambda: "postgres://lab")
    monkeypatch.setattr(
        migration.workspaces, "lab_immutability_status",
        lambda: {"database_enforced": True},
    )
    result = migration.apply(assume_yes=True)
    assert result["applied"] is False
    assert result["already_enforced"] is True
    assert result["verified"] is True


def test_rollback_is_narrow_and_requires_explicit_approval(monkeypatch):
    with pytest.raises(
        migration.LabImmutabilityMigrationBlocked,
        match="explicit_human_approval",
    ):
        migration.rollback()

    connection = _Connection()
    monkeypatch.setattr(migration.postgres_db, "_lab_database_url", lambda: "postgres://lab")
    monkeypatch.setattr(
        migration.postgres_db, "lab_connect",
        lambda: _Context(connection),
    )
    monkeypatch.setattr(
        migration.workspaces, "lab_immutability_status",
        lambda: {"protective_trigger_present": False},
    )
    result = migration.rollback(assume_yes=True)
    assert result["rolled_back"] is True
    assert result["verified"] is True
    sql = "\n".join(statement for statement, _ in connection.sql)
    assert "DROP TRIGGER IF EXISTS oap_lab_workspace_immutable" in sql
    assert "DROP FUNCTION IF EXISTS oap_lab_workspace_immutable_guard" in sql
    assert "DROP TABLE" not in sql
