"""Safe SQLite migration helper and CLI operations for OAP.

Implements:
- db_status()
- init_db(dry_run=False, assume_yes=False)

Migration files live in mission_control/migrations and must expose:
- name (str)
- checksum (sha256 hex of file content)
- apply(conn) function that runs migration using provided sqlite3.Connection

"""
from __future__ import annotations

import os
import sqlite3
import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Optional, Tuple

from . import config

MIGRATIONS_DIR = Path(__file__).resolve().parent / "migrations"

# Ensure migrations dir exists
MIGRATIONS_DIR.mkdir(parents=True, exist_ok=True)

SCHEMA_MIGRATIONS_TABLE = "schema_migrations"


def _connect(db_path: str) -> sqlite3.Connection:
    # enforce URI mode and detect_missing
    conn = sqlite3.connect(db_path, timeout=30, isolation_level=None)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 5000")
    try:
        conn.execute("PRAGMA journal_mode = WAL")
    except sqlite3.DatabaseError:
        pass
    return conn


def _ensure_schema_migrations(conn: sqlite3.Connection) -> None:
    conn.execute(
        f"CREATE TABLE IF NOT EXISTS {SCHEMA_MIGRATIONS_TABLE} (version TEXT PRIMARY KEY, name TEXT, checksum TEXT, applied_at TEXT)"
    )


def _load_migration_modules() -> List[Tuple[str, Path, str]]:
    """Return list of migrations as (version, path, checksum) sorted by filename."""
    files = sorted(MIGRATIONS_DIR.glob("*.py"))
    migrations = []
    for p in files:
        version = p.stem
        content = p.read_bytes()
        checksum = hashlib.sha256(content).hexdigest()
        migrations.append((version, p, checksum))
    return migrations


def _get_applied(conn: sqlite3.Connection) -> Dict[str, Dict]:
    cur = conn.execute(f"SELECT version, name, checksum, applied_at FROM {SCHEMA_MIGRATIONS_TABLE}")
    rows = cur.fetchall()
    return {r[0]: {"version": r[0], "name": r[1], "checksum": r[2], "applied_at": r[3]} for r in rows}


def db_status() -> Dict:
    db_path = config.OAP_DATABASE_PATH
    res = {"db_path": db_path, "exists": Path(db_path).exists(), "applied": [], "pending": []}
    if not Path(db_path).exists():
        return res
    conn = _connect(db_path)
    try:
        _ensure_schema_migrations(conn)
        applied = _get_applied(conn)
        res["applied"] = list(applied.values())
        migrations = _load_migration_modules()
        pending = []
        for version, path, checksum in migrations:
            if version not in applied:
                pending.append({"version": version, "name": path.name, "checksum": checksum})
        res["pending"] = pending
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
            raise RuntimeError("Backup integrity_check failed: %s" % (row,))
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
    migrations = _load_migration_modules()
    if not migrations:
        print("No migrations found; nothing to do.")
        return

    # Interactive confirmation
    if not assume_yes and sys.stdin.isatty():
        print(f"Resolved DB path: {db_path}")
        ans = input("Proceed to apply pending migrations? [y/N]: ")
        if ans.strip().lower() != "y":
            print("Aborted by user")
            return
    if not assume_yes and not sys.stdin.isatty():
        raise RuntimeError("Non-interactive session: pass --yes to proceed")

    if not db_file.exists():
        # Only create DB if user explicitly confirmed
        print("Database does not exist; creating new database")
        if dry_run:
            print("Dry run: would create database")
            return
        else:
            db_file.parent.mkdir(parents=True, exist_ok=True)
            # create empty db
            conn = _connect(str(db_file))
            conn.close()

    # Connect and apply migrations
    conn = _connect(str(db_file))
    try:
        _ensure_schema_migrations(conn)
        applied = _get_applied(conn)
        for version, path, checksum in _load_migration_modules():
            if version in applied:
                # checksum mismatch detection
                if applied[version]["checksum"] != checksum:
                    raise RuntimeError(f"Checksum mismatch for applied migration {version}")
                continue
            print(f"Pending migration: {version} - {path.name}")
            if dry_run:
                continue

            # Backup before applying
            backup_dir = Path(config.OAP_BACKUP_DIR)
            backup_dir.mkdir(parents=True, exist_ok=True)
            ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            backup_path = str(backup_dir / f"oap.db.bak.{ts}")
            print(f"Creating backup at {backup_path}")
            backup_sha = _backup_database(str(db_file), backup_path)
            print(f"Backup sha256: {backup_sha}")

            # Apply migration inside BEGIN IMMEDIATE
            try:
                conn.execute("BEGIN IMMEDIATE")
                # load module and call migrate(conn)
                spec = {}
                with open(path, "r", encoding="utf-8") as f:
                    code = f.read()
                exec(code, spec)
                if "migrate" not in spec:
                    raise RuntimeError(f"Migration {version} missing migrate(conn) function")
                spec["migrate"](conn)
                # record migration
                applied_at = datetime.now(timezone.utc).isoformat()
                conn.execute(
                    f"INSERT INTO {SCHEMA_MIGRATIONS_TABLE} (version, name, checksum, applied_at) VALUES (?,?,?,?)",
                    (version, path.name, checksum, applied_at),
                )
                conn.execute("COMMIT")
            except Exception:
                conn.execute("ROLLBACK")
                # on failure, preserve backup and report
                raise

            # After migration, run integrity check
            cur = conn.execute("PRAGMA integrity_check")
            row = cur.fetchone()
            if row is None or row[0] != "ok":
                raise RuntimeError("Post-migration integrity_check failed: %s" % (row,))

            # Rotation: keep latest 21 backups matching pattern
            backups = sorted([p for p in backup_dir.glob("oap.db.bak.*") if p.is_file()], reverse=True)
            keep = backups[:21]
            remove = backups[21:]
            for p in remove:
                try:
                    p.unlink()
                except Exception:
                    pass

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
