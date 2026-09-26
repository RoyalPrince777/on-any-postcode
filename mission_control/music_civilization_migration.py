"""Governed idempotent schema migration for OAP Music Civilization 0007-0012."""
from __future__ import annotations

import hashlib
import os

from . import (
    live_music_core,
    music_acceptance,
    music_evidence,
    music_recovery,
    postgres_db,
    radio_core,
    records_core,
)

_MIGRATIONS = (
    (music_evidence.MUSIC_EVIDENCE_MIGRATION_VERSION, music_evidence.SCHEMA_STATEMENTS),
    (radio_core.RADIO_MIGRATION_VERSION, radio_core.SCHEMA_STATEMENTS),
    (records_core.RECORDS_MIGRATION_VERSION, records_core.SCHEMA_STATEMENTS),
    (live_music_core.LIVE_MUSIC_MIGRATION_VERSION, live_music_core.SCHEMA_STATEMENTS),
    (music_recovery.RECOVERY_MIGRATION_VERSION, music_recovery.SCHEMA_STATEMENTS),
    (music_acceptance.ACCEPTANCE_MIGRATION_VERSION, music_acceptance.SCHEMA_STATEMENTS),
)
_LOCK_KEY = 25800012


def _checksum(statements: tuple[str, ...]) -> str:
    return hashlib.sha256("\n".join(statements).encode()).hexdigest()


def apply(*, assume_yes: bool = False) -> dict[str, object]:
    if not assume_yes:
        raise RuntimeError("Explicit human approval required")
    applied: list[str] = []
    existing: list[str] = []
    with postgres_db.connect() as connection:
        connection.execute("SELECT pg_advisory_xact_lock(%s)", (_LOCK_KEY,))
        for version, statements in _MIGRATIONS:
            checksum = _checksum(statements)
            row = connection.execute(
                "SELECT checksum FROM oap_schema_migrations WHERE version=%s",
                (version,),
            ).fetchone()
            if row is not None:
                if str(row[0]) != checksum:
                    raise RuntimeError(f"Migration checksum mismatch: {version}")
                existing.append(version)
                continue
            for statement in statements:
                connection.execute(statement)
            connection.execute(
                "INSERT INTO oap_schema_migrations(version,checksum) VALUES (%s,%s)",
                (version, checksum),
            )
            applied.append(version)
        connection.commit()
    return {
        "applied": applied,
        "existing": existing,
        "versions": [version for version, _ in _MIGRATIONS],
        "schema_ready": True,
    }


def apply_from_environment() -> dict[str, object] | None:
    if os.environ.get("OAP_MUSIC_SCHEMA_AUTO_APPLY") != "1":
        return None
    return apply(assume_yes=True)
