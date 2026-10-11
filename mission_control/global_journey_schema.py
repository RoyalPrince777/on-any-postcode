"""Opt-in schema definition for Global Movement associations.

No migration executes on import. Production rollout requires governed approval.
"""
from __future__ import annotations

import hashlib

MIGRATION_VERSION = "0001_oap_global_journey_associations"
STATEMENTS = (
    """CREATE TABLE IF NOT EXISTS oap_global_journey_associations (
        journey_id UUID PRIMARY KEY,
        booking_id UUID NOT NULL UNIQUE REFERENCES oap_movement_bookings(booking_id) ON DELETE RESTRICT,
        intent_id TEXT UNIQUE,
        version INTEGER NOT NULL CHECK (version = 1),
        owner_identity_id UUID NOT NULL REFERENCES oap_identities(identity_id),
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        CHECK (intent_id IS NULL OR intent_id ~ '^oap-book-[0-9a-f]{16}$')
    )""",
)
CHECKSUM = hashlib.sha256("\n".join(STATEMENTS).encode()).hexdigest()


def init_schema(*, assume_yes: bool = False, dry_run: bool = False) -> dict[str, object]:
    """Explicit, checksum-governed migration; never runs at import time."""
    if not assume_yes:
        raise RuntimeError("explicit_human_approval_required")
    if dry_run:
        return {"dry_run": True, "migration": MIGRATION_VERSION, "checksum": CHECKSUM}
    from . import postgres_db

    with postgres_db.connect() as connection:
        connection.execute("SELECT pg_advisory_xact_lock(%s)", (25800120,))
        row = connection.execute(
            "SELECT checksum FROM oap_schema_migrations WHERE version=%s",
            (MIGRATION_VERSION,),
        ).fetchone()
        if row is not None and str(row[0]) != CHECKSUM:
            raise RuntimeError("global_journey_migration_checksum_mismatch")
        if row is None:
            for statement in STATEMENTS:
                connection.execute(statement)
            connection.execute(
                "INSERT INTO oap_schema_migrations(version,checksum) VALUES (%s,%s)",
                (MIGRATION_VERSION, CHECKSUM),
            )
        connection.commit()
    return {"migration": MIGRATION_VERSION, "checksum": CHECKSUM, "applied": True}


def schema_status() -> dict[str, object]:
    """Read-only production evidence; migration receipt and table must agree."""
    from . import postgres_db

    try:
        with postgres_db.connect(readonly=True) as connection:
            row = connection.execute(
                "SELECT checksum FROM oap_schema_migrations WHERE version=%s",
                (MIGRATION_VERSION,),
            ).fetchone()
            if row is None or str(row[0]) != CHECKSUM:
                return {"schema_ready": False, "reason": "migration_unverified"}
            table = connection.execute(
                "SELECT to_regclass('public.oap_global_journey_associations')"
            ).fetchone()
            if table is None or table[0] is None:
                return {"schema_ready": False, "reason": "association_table_missing"}
            return {"schema_ready": True, "migration": MIGRATION_VERSION}
    except Exception:
        return {"schema_ready": False, "reason": "store_unavailable"}
