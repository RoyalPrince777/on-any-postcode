"""Canonical persisted links for Commerce → Movement → Post Core.

This module does not create orders, bookings, parcels, payments, dispatches or
carrier actions. It only records a first-party association after all three
canonical records are already present and owned by the authenticated identity.
"""
from __future__ import annotations

import hashlib
from typing import Any
from uuid import UUID

from . import postgres_db

LINK_SCHEMA_VERSION = "distribution_market_links_v1"
LINK_SCHEMA_STATEMENTS = (
    """CREATE TABLE IF NOT EXISTS oap_distribution_market_links (
        link_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        owner_identity_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
        order_id UUID NOT NULL UNIQUE
            REFERENCES oap_commerce_orders(order_id) ON DELETE CASCADE,
        booking_id UUID NOT NULL UNIQUE
            REFERENCES oap_movement_bookings(booking_id) ON DELETE CASCADE,
        parcel_id UUID NOT NULL UNIQUE
            REFERENCES oap_post_office_parcels(parcel_id) ON DELETE CASCADE,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(owner_identity_id, order_id, booking_id, parcel_id))""",
    """CREATE INDEX IF NOT EXISTS ix_distribution_market_links_owner_created
        ON oap_distribution_market_links(owner_identity_id, created_at DESC)""",
)
LINK_SCHEMA_CHECKSUM = hashlib.sha256(
    "\n".join(LINK_SCHEMA_STATEMENTS).encode()
).hexdigest()
LINK_SCHEMA_LOCK_KEY = 25800761
LINK_TABLE = "oap_distribution_market_links"
LINK_INDEX = "ix_distribution_market_links_owner_created"


class DistributionMarketLinkDenied(ValueError):
    """Requested link is incomplete, inconsistent or unauthorised."""


def _uuid(value: object, name: str) -> str:
    try:
        return str(UUID(str(value)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise DistributionMarketLinkDenied(f"invalid_{name}") from exc


def _owned_records(connection: Any, owner: str, order: str, booking: str, parcel: str) -> None:
    order_row = connection.execute(
        """SELECT 1 FROM oap_commerce_orders
           WHERE order_id=%s AND buyer_identity_id=%s LIMIT 1""",
        (order, owner),
    ).fetchone()
    booking_row = connection.execute(
        """SELECT 1 FROM oap_movement_bookings
           WHERE booking_id=%s AND member_identity_id=%s LIMIT 1""",
        (booking, owner),
    ).fetchone()
    parcel_row = connection.execute(
        """SELECT 1 FROM oap_post_office_parcels
           WHERE parcel_id=%s AND owner_identity_id=%s LIMIT 1""",
        (parcel, owner),
    ).fetchone()
    if order_row is None or booking_row is None or parcel_row is None:
        raise PermissionError("canonical_owner_mismatch")


def create_link(
    *,
    owner_identity_id: object,
    order_id: object,
    booking_id: object,
    parcel_id: object,
    stopped: bool = False,
) -> dict[str, object]:
    """Persist one canonical association without performing external actions."""
    if stopped:
        raise DistributionMarketLinkDenied("stopped")
    owner = _uuid(owner_identity_id, "owner_identity_id")
    order = _uuid(order_id, "order_id")
    booking = _uuid(booking_id, "booking_id")
    parcel = _uuid(parcel_id, "parcel_id")

    with postgres_db.connect() as connection:
        _owned_records(connection, owner, order, booking, parcel)
        existing = connection.execute(
            """SELECT order_id,booking_id,parcel_id
               FROM oap_distribution_market_links
               WHERE owner_identity_id=%s
                 AND (order_id=%s OR booking_id=%s OR parcel_id=%s)
               FOR UPDATE""",
            (owner, order, booking, parcel),
        ).fetchall()
        for row in existing:
            current = tuple(str(value) for value in row)
            if current != (order, booking, parcel):
                raise DistributionMarketLinkDenied("link_reference_reused")
        if existing:
            created = False
        else:
            connection.execute(
                """INSERT INTO oap_distribution_market_links
                   (owner_identity_id,order_id,booking_id,parcel_id)
                   VALUES (%s,%s,%s,%s)""",
                (owner, order, booking, parcel),
            )
            created = True
        connection.commit()
    return {
        "owner_identity_id": owner,
        "order_id": order,
        "booking_id": booking,
        "parcel_id": parcel,
        "created": created,
        "payment_capture_performed": False,
        "dispatch_performed": False,
        "carrier_handoff_performed": False,
        "human_authority_final": True,
    }


def read_link(*, owner_identity_id: object, order_id: object) -> dict[str, object]:
    """Read back one association under the same owner scope."""
    owner = _uuid(owner_identity_id, "owner_identity_id")
    order = _uuid(order_id, "order_id")
    with postgres_db.connect(readonly=True) as connection:
        row = connection.execute(
            """SELECT order_id,booking_id,parcel_id,created_at
               FROM oap_distribution_market_links
               WHERE owner_identity_id=%s AND order_id=%s""",
            (owner, order),
        ).fetchone()
    if row is None:
        raise PermissionError("canonical_link_not_owned")
    return {
        "owner_identity_id": owner,
        "order_id": str(row[0]),
        "booking_id": str(row[1]),
        "parcel_id": str(row[2]),
        "created_at": row[3].isoformat(),
        "payment_capture_performed": False,
        "dispatch_performed": False,
        "carrier_handoff_performed": False,
        "human_authority_final": True,
    }


def schema_status() -> dict[str, object]:
    """Read-only readiness for the canonical Distribution × Market link schema."""
    result: dict[str, object] = {
        "migration": LINK_SCHEMA_VERSION,
        "checksum": LINK_SCHEMA_CHECKSUM,
        "schema_ready": False,
        "table_ready": False,
        "index_ready": False,
        "migration_recorded": False,
        "error": None,
    }
    try:
        with postgres_db.connect(readonly=True) as connection:
            table = connection.execute(
                """SELECT 1 FROM information_schema.tables
                   WHERE table_schema='public' AND table_name=%s""",
                (LINK_TABLE,),
            ).fetchone()
            index = connection.execute(
                """SELECT 1 FROM pg_indexes
                   WHERE schemaname='public' AND indexname=%s""",
                (LINK_INDEX,),
            ).fetchone()
            migration = connection.execute(
                "SELECT checksum FROM oap_schema_migrations WHERE version=%s",
                (LINK_SCHEMA_VERSION,),
            ).fetchone()
    except Exception:  # noqa: BLE001 - readiness is redacted and fail-closed.
        result["error"] = "distribution_market_schema_unavailable"
        return result

    result["table_ready"] = table is not None
    result["index_ready"] = index is not None
    result["migration_recorded"] = migration is not None
    if migration is not None and str(migration[0]) != LINK_SCHEMA_CHECKSUM:
        result["error"] = "distribution_market_schema_checksum_mismatch"
    elif not all((table, index, migration)):
        result["error"] = "distribution_market_schema_pending"
    else:
        result["schema_ready"] = True
    return result


def init_link_schema(*, assume_yes: bool = False, dry_run: bool = True) -> dict[str, object]:
    """Apply the link schema transactionally after explicit Human Authority approval."""
    if not assume_yes:
        raise RuntimeError("Explicit human approval required: pass --yes")
    if dry_run:
        return {
            "dry_run": True,
            "migration": LINK_SCHEMA_VERSION,
            "checksum": LINK_SCHEMA_CHECKSUM,
            "statements": len(LINK_SCHEMA_STATEMENTS),
            "applied": False,
        }

    with postgres_db.connect() as connection:
        try:
            connection.execute(
                "SELECT pg_advisory_xact_lock(%s)",
                (LINK_SCHEMA_LOCK_KEY,),
            )
            existing = connection.execute(
                "SELECT checksum FROM oap_schema_migrations WHERE version=%s",
                (LINK_SCHEMA_VERSION,),
            ).fetchone()
            if existing is not None and str(existing[0]) != LINK_SCHEMA_CHECKSUM:
                raise RuntimeError("distribution_market_schema_checksum_mismatch")
            applied = existing is None
            if applied:
                for statement in LINK_SCHEMA_STATEMENTS:
                    connection.execute(statement)
                connection.execute(
                    """INSERT INTO oap_schema_migrations(version,checksum)
                       VALUES (%s,%s)""",
                    (LINK_SCHEMA_VERSION, LINK_SCHEMA_CHECKSUM),
                )
            connection.commit()
        except Exception:
            connection.rollback()
            raise

    status = schema_status()
    if status.get("schema_ready") is not True:
        raise RuntimeError("distribution_market_schema_not_ready_after_migration")
    return {
        **status,
        "dry_run": False,
        "statements": len(LINK_SCHEMA_STATEMENTS),
        "applied": applied,
    }
