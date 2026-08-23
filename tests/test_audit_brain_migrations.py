from __future__ import annotations

import hashlib
import json
import sqlite3

import pytest

from mission_control import audit, config, db


def test_explicit_migrations_initialize_audit_and_brain_runtime(
    tmp_path, monkeypatch
):
    database_path = tmp_path / "oap-runtime.db"
    backup_path = tmp_path / "backups"
    monkeypatch.setattr(config, "OAP_DATABASE_PATH", str(database_path))
    monkeypatch.setattr(config, "OAP_BACKUP_DIR", str(backup_path))

    db.init_db(assume_yes=True)
    status = db.db_status()

    assert status["initialized"] is True
    assert status["brain_runtime_initialized"] is True
    assert status["pending"] == []
    assert {item["version"] for item in status["applied"]} == {
        "0001_audit_foundation",
        "0002_smi_brain_runtime",
    }
    assert len(list(backup_path.glob("oap.db.bak.*"))) == 2

    connection = sqlite3.connect(database_path)
    tables = {
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        )
    }
    connection.close()
    assert {
        "audit_events",
        "schema_migrations",
        "smi_memory_records",
        "smi_approval_receipts",
        "smi_kernel_outcomes",
        "smi_world_state",
    } <= tables


def test_audit_chain_redacts_nested_secrets_and_detects_tampering(
    tmp_path, monkeypatch
):
    database_path = tmp_path / "audit.db"
    monkeypatch.setattr(config, "OAP_DATABASE_PATH", str(database_path))
    monkeypatch.setattr(config, "OAP_BACKUP_DIR", str(tmp_path / "backups"))
    db.init_db(assume_yes=True)

    connection = sqlite3.connect(database_path)
    audit.append_event(
        connection,
        actor="founder-1",
        actor_type="human_authority",
        authority_level=0,
        action="HUMAN_APPROVED",
        target="request-1",
        reason="Approved test",
        metadata={"nested": {"token": "hide", "safe": "keep"}},
    )
    audit.append_event(
        connection,
        actor="Living Kernel",
        actor_type="kernel",
        authority_level=1,
        action="KERNEL_EXECUTED",
        target="request-1",
        reason="Completed test",
        metadata={},
    )
    metadata = json.loads(
        connection.execute(
            "SELECT metadata FROM audit_events WHERE event_seq = 1"
        ).fetchone()[0]
    )
    connection.close()

    assert metadata == {"nested": {"safe": "keep", "token": "<REDACTED>"}}
    assert audit.verify_audit(str(database_path)) == (True, ["OK"])

    connection = sqlite3.connect(database_path)
    connection.execute(
        "UPDATE audit_events SET reason = 'tampered' WHERE event_seq = 1"
    )
    connection.commit()
    connection.close()

    valid, problems = audit.verify_audit(str(database_path))
    assert valid is False
    assert any("Hash mismatch" in problem for problem in problems)


def test_audit_verification_is_read_only(tmp_path, monkeypatch):
    database_path = tmp_path / "audit-readonly.db"
    monkeypatch.setattr(config, "OAP_DATABASE_PATH", str(database_path))
    monkeypatch.setattr(config, "OAP_BACKUP_DIR", str(tmp_path / "backups"))
    db.init_db(assume_yes=True)
    before = hashlib.sha256(database_path.read_bytes()).hexdigest()
    before_stat = database_path.stat()

    assert audit.verify_audit(str(database_path)) == (True, ["OK"])

    after = hashlib.sha256(database_path.read_bytes()).hexdigest()
    after_stat = database_path.stat()
    assert before == after
    assert before_stat.st_size == after_stat.st_size
    assert before_stat.st_mtime_ns == after_stat.st_mtime_ns


def test_migration_dry_run_never_creates_or_changes_database(
    tmp_path,
    monkeypatch,
):
    missing_path = tmp_path / "missing.db"
    monkeypatch.setattr(config, "OAP_DATABASE_PATH", str(missing_path))
    monkeypatch.setattr(config, "OAP_BACKUP_DIR", str(tmp_path / "backups"))

    db.init_db(dry_run=True)

    assert not missing_path.exists()
    existing_path = tmp_path / "existing.db"
    connection = sqlite3.connect(existing_path)
    connection.execute("CREATE TABLE existing_data (value TEXT NOT NULL)")
    connection.execute("INSERT INTO existing_data VALUES ('preserve')")
    connection.commit()
    connection.close()
    before = hashlib.sha256(existing_path.read_bytes()).hexdigest()
    before_stat = existing_path.stat()
    monkeypatch.setattr(config, "OAP_DATABASE_PATH", str(existing_path))

    db.init_db(dry_run=True)

    after = hashlib.sha256(existing_path.read_bytes()).hexdigest()
    after_stat = existing_path.stat()
    assert before == after
    assert before_stat.st_mtime_ns == after_stat.st_mtime_ns
    connection = sqlite3.connect(existing_path)
    tables = {
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        )
    }
    connection.close()
    assert tables == {"existing_data"}


def test_migration_refuses_incompatible_legacy_audit_without_replacing_it(
    tmp_path,
    monkeypatch,
):
    database_path = tmp_path / "legacy-audit.db"
    backup_path = tmp_path / "backups"
    connection = sqlite3.connect(database_path)
    connection.execute(
        "CREATE TABLE audit_events (id INTEGER PRIMARY KEY, action TEXT)"
    )
    connection.execute("INSERT INTO audit_events VALUES (1, 'preserve')")
    connection.commit()
    connection.close()
    original_hash = hashlib.sha256(database_path.read_bytes()).hexdigest()
    monkeypatch.setattr(config, "OAP_DATABASE_PATH", str(database_path))
    monkeypatch.setattr(config, "OAP_BACKUP_DIR", str(backup_path))

    with pytest.raises(RuntimeError, match="incompatible"):
        db.init_db(assume_yes=True)

    assert hashlib.sha256(database_path.read_bytes()).hexdigest() == original_hash
    connection = sqlite3.connect(database_path)
    columns = {
        row[1] for row in connection.execute("PRAGMA table_info(audit_events)")
    }
    migration_table = connection.execute(
        "SELECT 1 FROM sqlite_master "
        "WHERE type = 'table' AND name = 'schema_migrations'"
    ).fetchone()
    connection.close()
    assert columns == {"id", "action"}
    assert migration_table is None
    assert len(list(backup_path.glob("oap.db.bak.*"))) == 1


def test_status_fails_closed_on_applied_migration_checksum_mismatch(
    tmp_path,
    monkeypatch,
):
    database_path = tmp_path / "checksum.db"
    monkeypatch.setattr(config, "OAP_DATABASE_PATH", str(database_path))
    monkeypatch.setattr(config, "OAP_BACKUP_DIR", str(tmp_path / "backups"))
    db.init_db(assume_yes=True)
    connection = sqlite3.connect(database_path)
    connection.execute(
        "UPDATE schema_migrations SET checksum = 'tampered' "
        "WHERE version = '0001_audit_foundation'"
    )
    connection.commit()
    connection.close()

    migration_status = db.db_status()

    assert migration_status["initialized"] is False
    assert migration_status["brain_runtime_initialized"] is False
    assert migration_status["error"] == "migration_checksum_mismatch"
    assert migration_status["checksum_mismatches"] == ["0001_audit_foundation"]
