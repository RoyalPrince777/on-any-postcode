"""Opt-in schema definition for Global Movement associations.

No migration executes on import. Production rollout requires governed approval.
"""
from __future__ import annotations

import hashlib

import psycopg

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
LIFECYCLE_VERSION = "0002_oap_journey_cancellation_receipts"
LIFECYCLE_STATEMENTS = (
    """CREATE TABLE IF NOT EXISTS oap_journey_cancellations (
        booking_id UUID PRIMARY KEY REFERENCES oap_movement_bookings(booking_id) ON DELETE RESTRICT,
        actor_identity_id UUID NOT NULL REFERENCES oap_identities(identity_id),
        prior_state TEXT NOT NULL,
        cancelled_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP)""",
)
LIFECYCLE_CHECKSUM = hashlib.sha256("\n".join(LIFECYCLE_STATEMENTS).encode()).hexdigest()


def init_schema(*, assume_yes: bool = False, dry_run: bool = False) -> dict[str, object]:
    """Explicit, checksum-governed migration; never runs at import time."""
    if not assume_yes:
        raise RuntimeError("explicit_human_approval_required")
    if dry_run:
        return {"dry_run": True, "migration": MIGRATION_VERSION, "checksum": CHECKSUM,
                "lifecycle_migration": LIFECYCLE_VERSION, "lifecycle_checksum": LIFECYCLE_CHECKSUM}
    from . import postgres_db

    with postgres_db.connect() as connection:
        connection.execute("SET TRANSACTION ISOLATION LEVEL READ COMMITTED")
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
        lifecycle = connection.execute("SELECT checksum FROM oap_schema_migrations WHERE version=%s", (LIFECYCLE_VERSION,)).fetchone()
        if lifecycle is not None and str(lifecycle[0]) != LIFECYCLE_CHECKSUM:
            raise RuntimeError("journey_lifecycle_migration_checksum_mismatch")
        if lifecycle is None:
            for statement in LIFECYCLE_STATEMENTS:
                connection.execute(statement)
            connection.execute("INSERT INTO oap_schema_migrations(version,checksum) VALUES (%s,%s)", (LIFECYCLE_VERSION, LIFECYCLE_CHECKSUM))
        connection.execute("SELECT journey_id,booking_id,owner_identity_id,version,intent_id FROM oap_global_journey_associations LIMIT 0")
        connection.execute("SELECT booking_id,actor_identity_id,prior_state,cancelled_at FROM oap_journey_cancellations LIMIT 0")
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
    except (OSError, RuntimeError, psycopg.Error):
        return {"schema_ready": False, "reason": "store_unavailable"}
