"""Safe SQLite migration helper and CLI operations for OAP.

Implements:
- db_status()
- init_db(dry_run=False, assume_yes=False)

Migration files live in mission_control/migrations and must expose:
- migrate(conn) function that runs inside the transaction owned by this helper

"""
from __future__ import annotations

import hashlib
import importlib.util
import os
import sqlite3
import sys
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import psycopg

from oap.audit import audit_schema_ready
from oap.database import execute, integrity_ready, table_exists
from oap.hrm import brain_schema_ready

from . import config

MIGRATIONS_DIR = Path(__file__).resolve().parent / "migrations"

SCHEMA_MIGRATIONS_TABLE = "schema_migrations"
MigrationFunction = Callable[[Any], None]


def _connect_sqlite(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path, timeout=30, isolation_level=None)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 5000")
    return conn


def _connect_sqlite_readonly(db_path: str) -> sqlite3.Connection:
    """Open an existing database without creating files or changing pragmas."""

    uri = Path(db_path).resolve().as_uri() + "?mode=ro"
    conn = sqlite3.connect(uri, uri=True, timeout=1)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA query_only = ON")
    conn.execute("PRAGMA busy_timeout = 250")
    return conn


def _connect(*, readonly: bool = False):
    if config.DATABASE_BACKEND == "postgresql":
        from psycopg.rows import dict_row

        connection = psycopg.connect(
            config.DATABASE_URL,
            autocommit=True,
            row_factory=dict_row,
        )
        if readonly:
            connection.execute("SET default_transaction_read_only = on")
        return connection
    if readonly:
        return _connect_sqlite_readonly(config.OAP_DATABASE_PATH)
    return _connect_sqlite(config.OAP_DATABASE_PATH)


def connect_readonly():
    """Return a query-only connection without creating or migrating storage."""

    return _connect(readonly=True)


def _ensure_schema_migrations(conn: Any) -> None:
    conn.execute(
        f"CREATE TABLE IF NOT EXISTS {SCHEMA_MIGRATIONS_TABLE} (version TEXT PRIMARY KEY, name TEXT, checksum TEXT, applied_at TEXT)"
    )


def _load_migration_modules() -> list[tuple[str, Path, str]]:
    """Return list of migrations as (version, path, checksum) sorted by filename."""
    files = sorted(MIGRATIONS_DIR.glob("*.py"))
    migrations = []
    for p in files:
        version = p.stem
        content = p.read_bytes()
        checksum = hashlib.sha256(content).hexdigest()
        migrations.append((version, p, checksum))
    return migrations


def _load_migrate_function(path: Path) -> MigrationFunction:
    module_name = f"oap_migration_{path.stem}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load migration {path.name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    migrate = getattr(module, "migrate", None)
    if not callable(migrate):
        raise TypeError(f"Migration {path.stem} missing migrate(conn) function")
    return migrate


def _get_applied(conn: Any) -> dict[str, dict[str, str]]:
    cur = conn.execute(f"SELECT version, name, checksum, applied_at FROM {SCHEMA_MIGRATIONS_TABLE}")
    rows = cur.fetchall()
    return {r[0]: {"version": r[0], "name": r[1], "checksum": r[2], "applied_at": r[3]} for r in rows}


def _table_exists(conn: Any, table_name: str) -> bool:
    return table_exists(conn, table_name)


def db_status() -> dict[str, object]:
    db_path = config.OAP_DATABASE_PATH
    backend = config.DATABASE_BACKEND
    migrations = _load_migration_modules()
    res = {
        "backend": backend,
        "db_path": db_path if backend == "sqlite" else None,
        "exists": Path(db_path).is_file() if backend == "sqlite" else False,
        "initialized": False,
        "brain_runtime_initialized": False,
        "applied": [],
        "checksum_mismatches": [],
        "pending": [
            {"version": version, "name": path.name, "checksum": checksum}
            for version, path, checksum in migrations
        ],
        "error": None,
    }
    if backend == "sqlite" and not res["exists"]:
        return res

    try:
        conn = _connect(readonly=True)
        res["exists"] = True
    except (RuntimeError, sqlite3.Error, psycopg.Error, OSError):
        res["error"] = "database_unavailable"
        return res

    try:
        if not _table_exists(conn, SCHEMA_MIGRATIONS_TABLE):
            return res

        applied = _get_applied(conn)
        res["applied"] = list(applied.values())
        pending = []
        for version, path, checksum in migrations:
            if version not in applied:
                pending.append({"version": version, "name": path.name, "checksum": checksum})
            elif applied[version]["checksum"] != checksum:
                res["checksum_mismatches"].append(version)
        res["pending"] = pending
        checksums_valid = not res["checksum_mismatches"]
        if not checksums_valid:
            res["error"] = "migration_checksum_mismatch"
        res["initialized"] = checksums_valid and audit_schema_ready(conn) and any(
            version.startswith("0001_") for version in applied
        )
        res["brain_runtime_initialized"] = (
            checksums_valid
            and brain_schema_ready(conn)
            and any(version.startswith("0002_") for version in applied)
        )
        return res
    except (sqlite3.Error, psycopg.Error, OSError):
        res["error"] = "database_unavailable"
        return res
    finally:
        conn.close()


def _backup_database(src_path: str, dst_path: str) -> str:
    """Backup using SQLite online backup API. Returns sha256 hex of backup file."""
    src_conn = sqlite3.connect(src_path)
    dst_conn = sqlite3.connect(dst_path)
    try:
        # Use the backup API
        src_conn.backup(dst_conn)
        dst_conn.commit()
    finally:
        dst_conn.close()
        src_conn.close()

    # Run integrity_check on backup
    bconn = sqlite3.connect(dst_path)
    try:
        cur = bconn.execute("PRAGMA integrity_check")
        row = cur.fetchone()
        if row is None or row[0] != "ok":
            raise RuntimeError(f"Backup integrity_check failed: {row}")
    finally:
        bconn.close()

    # fsync destination file
    with open(dst_path, "rb") as f:
        data = f.read()
    sha = hashlib.sha256(data).hexdigest()
    return sha


def init_db(dry_run: bool = False, assume_yes: bool = False) -> None:
    db_path = config.OAP_DATABASE_PATH
    db_file = Path(db_path)
    backend = config.DATABASE_BACKEND
    migrations = _load_migration_modules()
    if not migrations:
        print("No migrations found; nothing to do.")
        return

    if dry_run:
        print(f"Resolved DB backend: {backend}")
        if backend == "sqlite":
            print(f"Resolved DB path: {db_path}")
        if backend == "sqlite" and not db_file.exists():
            print("Dry run: would create database and apply:")
            for version, path, _checksum in migrations:
                print(f"  - {version} ({path.name})")
            return

        conn = _connect(readonly=True)
        try:
            applied = (
                _get_applied(conn)
                if _table_exists(conn, SCHEMA_MIGRATIONS_TABLE)
                else {}
            )
            pending = []
            for version, path, checksum in migrations:
                if version in applied:
                    if applied[version]["checksum"] != checksum:
                        raise RuntimeError(
                            f"Checksum mismatch for applied migration {version}"
                        )
                    continue
                pending.append((version, path))
            if pending:
                print("Dry run: would apply:")
                for version, path in pending:
                    print(f"  - {version} ({path.name})")
            else:
                print("Dry run: no pending migrations")
        finally:
            conn.close()
        return

    # Interactive confirmation
    if not assume_yes and sys.stdin.isatty():
        print(f"Resolved DB backend: {backend}")
        if backend == "sqlite":
            print(f"Resolved DB path: {db_path}")
        ans = input("Proceed to apply pending migrations? [y/N]: ")
        if ans.strip().lower() != "y":
            print("Aborted by user")
            return
    if not assume_yes and not sys.stdin.isatty():
        raise RuntimeError("Non-interactive session: pass --yes to proceed")

    if backend == "sqlite" and not db_file.exists():
        # Only create DB if user explicitly confirmed
        print("Database does not exist; creating new database")
        db_file.parent.mkdir(parents=True, exist_ok=True)
        # create empty db
        conn = _connect()
        conn.close()

    # Connect and apply migrations
    conn = _connect()
    try:
        applied = (
            _get_applied(conn)
            if _table_exists(conn, SCHEMA_MIGRATIONS_TABLE)
            else {}
        )
        pending_exists = any(
            version not in applied for version, _path, _checksum in migrations
        )
        if (
            backend == "postgresql"
            and applied
            and pending_exists
            and os.environ.get("OAP_DATABASE_BACKUP_CONFIRMED", "").lower() != "true"
        ):
            raise RuntimeError(
                "PostgreSQL migration blocked: confirm a managed backup by setting "
                "OAP_DATABASE_BACKUP_CONFIRMED=true for this explicit migration run"
            )
        for version, path, checksum in _load_migration_modules():
            if version in applied:
                # checksum mismatch detection
                if applied[version]["checksum"] != checksum:
                    raise RuntimeError(f"Checksum mismatch for applied migration {version}")
                continue
            print(f"Pending migration: {version} - {path.name}")
            backup_dir = None
            if backend == "sqlite":
                backup_dir = Path(config.OAP_BACKUP_DIR)
                backup_dir.mkdir(parents=True, exist_ok=True)
                ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
                backup_path = str(backup_dir / f"oap.db.bak.{version}.{ts}")
                print(f"Creating backup at {backup_path}")
                backup_sha = _backup_database(str(db_file), backup_path)
                print(f"Backup sha256: {backup_sha}")

            # Apply migration inside BEGIN IMMEDIATE
            try:
                conn.execute("BEGIN" if backend == "postgresql" else "BEGIN IMMEDIATE")
                _ensure_schema_migrations(conn)
                migrate = _load_migrate_function(path)
                migrate(conn)
                # record migration
                applied_at = datetime.now(timezone.utc).isoformat()
                execute(
                    conn,
                    f"INSERT INTO {SCHEMA_MIGRATIONS_TABLE} (version, name, checksum, applied_at) VALUES (?,?,?,?)",
                    (version, path.name, checksum, applied_at),
                )
                conn.execute("COMMIT")
            except Exception:
                conn.execute("ROLLBACK")
                # on failure, preserve backup and report
                raise

            # After migration, run integrity check
            if not integrity_ready(conn):
                raise RuntimeError("Post-migration integrity check failed")

            # Rotation: keep latest 21 backups matching pattern
            if backup_dir is not None:
                backups = sorted(
                    [p for p in backup_dir.glob("oap.db.bak.*") if p.is_file()],
                    reverse=True,
                )
                remove = backups[21:]
                for p in remove:
                    try:
                        p.unlink()
                    except OSError as exc:
                        print(f"Warning: could not remove old backup {p}: {exc}")

        if not audit_schema_ready(conn) or not brain_schema_ready(conn):
            raise RuntimeError(
                "Migration records exist but the canonical runtime schema is "
                "incomplete or incompatible"
            )

        # Configure WAL only after every pending migration has succeeded.
        if backend == "sqlite":
            conn.execute("PRAGMA journal_mode = WAL")

    finally:
        conn.close()


# Minimal CLI-friendly wrapper for status
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--status", action="store_true")
    args = parser.parse_args()
    if args.status:
        print(db_status())
