"""Immutable commercial split snapshot for completed OAP Ride journeys."""
from __future__ import annotations

import hashlib
from typing import Any
from uuid import UUID

from . import oap_ride_commercial, postgres_db

MIGRATION = "0009_oap_ride_split_snapshot"
TABLES = frozenset({"oap_ride_split_snapshots"})
STATEMENTS = (
    """CREATE TABLE IF NOT EXISTS oap_ride_split_snapshots (
        booking_id UUID PRIMARY KEY REFERENCES oap_movement_bookings(booking_id) ON DELETE CASCADE,
        rule_id TEXT,
        driver_basis_points INTEGER,
        platform_basis_points INTEGER,
        driver_earnings_minor BIGINT,
        platform_amount_minor BIGINT,
        gross_amount_minor BIGINT,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        CHECK (
          (rule_id IS NULL AND driver_basis_points IS NULL AND platform_basis_points IS NULL)
          OR
          (driver_basis_points BETWEEN 0 AND 10000
           AND platform_basis_points BETWEEN 0 AND 10000
           AND driver_basis_points + platform_basis_points = 10000)
        ))""",
)
CHECKSUM = hashlib.sha256("\n".join(STATEMENTS).encode()).hexdigest()


def _uuid(value: object, name: str) -> str:
    try:
        return str(UUID(str(value)))
    except Exception as exc:
        raise ValueError(f"invalid_{name}") from exc


def init_schema(*, assume_yes: bool = False, dry_run: bool = False) -> dict[str, Any]:
    if not assume_yes:
        raise RuntimeError("explicit_human_approval_required")
    if dry_run:
        return {"dry_run": True, "migration": MIGRATION, "checksum": CHECKSUM, "tables": 1}
    with postgres_db.connect() as c:
        c.execute("SELECT pg_advisory_xact_lock(%s)", (25800029,))
        row = c.execute(
            "SELECT checksum FROM oap_schema_migrations WHERE version=%s", (MIGRATION,)
        ).fetchone()
        if row is not None and str(row[0]) != CHECKSUM:
            raise RuntimeError("ride_split_snapshot_migration_checksum_mismatch")
        if row is None:
            for stmt in STATEMENTS:
                c.execute(stmt)
            c.execute(
                "INSERT INTO oap_schema_migrations(version,checksum) VALUES (%s,%s)",
                (MIGRATION, CHECKSUM),
            )
        c.commit()
    return {"migration": MIGRATION, "schema_ready": True, "tables": 1}


def capture(*, booking_id: object, amount_minor: object | None) -> dict[str, Any]:
    booking = _uuid(booking_id, "booking_id")
    amount = None if amount_minor is None else int(amount_minor)
    if amount is not None and amount < 0:
        raise ValueError("invalid_amount_minor")
    rule = oap_ride_commercial.active_split()
    if rule is None or amount is None:
        values = (None, None, None, None, None)
    else:
        driver = (amount * int(rule["driver_basis_points"])) // 10000
        platform = amount - driver
        values = (
            rule["rule_id"],
            int(rule["driver_basis_points"]),
            int(rule["platform_basis_points"]),
            driver,
            platform,
        )
    with postgres_db.connect() as c:
        row = c.execute(
            """INSERT INTO oap_ride_split_snapshots
               (booking_id,rule_id,driver_basis_points,platform_basis_points,
                driver_earnings_minor,platform_amount_minor,gross_amount_minor)
               VALUES (%s,%s,%s,%s,%s,%s,%s)
               ON CONFLICT (booking_id) DO NOTHING
               RETURNING booking_id,rule_id,driver_basis_points,platform_basis_points,
                         driver_earnings_minor,platform_amount_minor,gross_amount_minor""",
            (booking, *values, amount),
        ).fetchone()
        if row is None:
            row = c.execute(
                """SELECT booking_id,rule_id,driver_basis_points,platform_basis_points,
                          driver_earnings_minor,platform_amount_minor,gross_amount_minor
                   FROM oap_ride_split_snapshots WHERE booking_id=%s""",
                (booking,),
            ).fetchone()
        c.commit()
    return {
        "booking_id": str(row[0]),
        "rule_id": str(row[1]) if row[1] else None,
        "driver_basis_points": int(row[2]) if row[2] is not None else None,
        "platform_basis_points": int(row[3]) if row[3] is not None else None,
        "driver_earnings_minor": int(row[4]) if row[4] is not None else None,
        "platform_amount_minor": int(row[5]) if row[5] is not None else None,
        "gross_amount_minor": int(row[6]) if row[6] is not None else None,
        "immutable": True,
        "settlement_performed": False,
    }


def read(*, booking_id: object) -> dict[str, Any] | None:
    booking = _uuid(booking_id, "booking_id")
    with postgres_db.connect(readonly=True) as c:
        row = c.execute(
            """SELECT rule_id,driver_basis_points,platform_basis_points,
                      driver_earnings_minor,platform_amount_minor,gross_amount_minor
               FROM oap_ride_split_snapshots WHERE booking_id=%s""",
            (booking,),
        ).fetchone()
    if row is None:
        return None
    return {
        "booking_id": booking,
        "rule_id": str(row[0]) if row[0] else None,
        "driver_basis_points": int(row[1]) if row[1] is not None else None,
        "platform_basis_points": int(row[2]) if row[2] is not None else None,
        "driver_earnings_minor": int(row[3]) if row[3] is not None else None,
        "platform_amount_minor": int(row[4]) if row[4] is not None else None,
        "gross_amount_minor": int(row[5]) if row[5] is not None else None,
        "immutable": True,
        "settlement_performed": False,
    }
