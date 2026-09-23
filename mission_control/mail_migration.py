"""Explicit, checksum-tracked migration for private OAP Mail.

Never runs on import, app startup, or ordinary mailbox reads.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from . import postgres_db

MAIL_MIGRATION_VERSION = "0010_oap_mail_items"
MAIL_TABLE = "oap_mail_items"
MAIL_INDEX = "idx_oap_mail_owner_folder_created"
MAIL_SQL_PATH = Path(__file__).resolve().parent.parent / "migrations" / "0006_oap_mail_items.sql"


def _statements() -> tuple[str, ...]:
    sql = MAIL_SQL_PATH.read_text(encoding="utf-8")
    cleaned = "\n".join(
        line for line in sql.splitlines() if not line.lstrip().startswith("--")
    )
    statements = tuple(part.strip() for part in cleaned.split(";") if part.strip())
    if len(statements) != 2 or not statements[0].startswith(
        "CREATE TABLE IF NOT EXISTS oap_mail_items ("
    ) or not statements[1].startswith(
        "CREATE INDEX IF NOT EXISTS idx_oap_mail_owner_folder_created"
    ):
        raise RuntimeError("mail_migration_sql_unrecognised")
    return statements


def _checksum(statements: tuple[str, ...]) -> str:
    return hashlib.sha256("\n".join(statements).encode()).hexdigest()


def schema_status() -> dict[str, Any]:
    statements = _statements()
    result = {
        "migration": MAIL_MIGRATION_VERSION,
        "checksum": _checksum(statements),
        "schema_ready": False,
        "table_ready": False,
        "index_ready": False,
        "error": None,
    }
    if not postgres_db.postgres_status().get("initialized"):
        result["error"] = "base_postgres_not_ready"
        return result
    try:
        with postgres_db.connect(readonly=True) as connection:
            table = connection.execute(
                """SELECT 1 FROM information_schema.tables
                   WHERE table_schema='public' AND table_name=%s""",
                (MAIL_TABLE,),
            ).fetchone()
            index = connection.execute(
                """SELECT 1 FROM pg_indexes
                   WHERE schemaname='public' AND indexname=%s""",
                (MAIL_INDEX,),
            ).fetchone()
            result["table_ready"] = table is not None
            result["index_ready"] = index is not None
            version = connection.execute(
                "SELECT checksum FROM oap_schema_migrations WHERE version=%s",
                (MAIL_MIGRATION_VERSION,),
            ).fetchone()
            if version is not None and str(version[0]) != result["checksum"]:
                result["error"] = "mail_migration_checksum_mismatch"
            elif not all((table, index, version)):
                result["error"] = "mail_migration_pending"
            else:
                result["schema_ready"] = True
    except Exception:  # noqa: BLE001 - return redacted readiness; never expose DB details.
        result["error"] = "mail_migration_store_unavailable"
    return result


def init_schema(*, assume_yes: bool = False, dry_run: bool = False) -> dict[str, Any]:
    if not assume_yes:
        raise RuntimeError("Explicit human approval required: pass --yes")
    statements = _statements()
    checksum = _checksum(statements)
    if dry_run:
        return {
            "dry_run": True,
            "migration": MAIL_MIGRATION_VERSION,
            "checksum": checksum,
            "statements": len(statements),
            "applied": False,
        }
    if not postgres_db.postgres_status().get("initialized"):
        raise RuntimeError("base_postgres_not_ready")
    with postgres_db.connect() as connection:
        try:
            connection.execute("SELECT pg_advisory_xact_lock(%s)", (25800010,))
            row = connection.execute(
                "SELECT checksum FROM oap_schema_migrations WHERE version=%s",
                (MAIL_MIGRATION_VERSION,),
            ).fetchone()
            if row is not None and str(row[0]) != checksum:
                raise RuntimeError("mail_migration_checksum_mismatch")
            if row is None:
                for statement in statements:
                    connection.execute(statement)
                connection.execute(
                    "INSERT INTO oap_schema_migrations(version,checksum) VALUES (%s,%s)",
                    (MAIL_MIGRATION_VERSION, checksum),
                )
            connection.commit()
        except Exception:
            connection.rollback()
            raise
    result = schema_status()
    if not result["schema_ready"]:
        raise RuntimeError("mail_schema_not_ready_after_migration")
    return result
