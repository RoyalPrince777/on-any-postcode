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


def init_link_schema(*, assume_yes: bool = False, dry_run: bool = True) -> dict[str, object]:
    """Prepare the association table only with explicit human approval.

    dry_run defaults True so importing/calling this module cannot mutate storage
    accidentally.
    """
    if not assume_yes:
        raise RuntimeError("Explicit human approval required: pass --yes")
    if dry_run:
        return {
            "dry_run": True,
            "migration": LINK_SCHEMA_VERSION,
            "checksum": LINK_SCHEMA_CHECKSUM,
            "statements": len(LINK_SCHEMA_STATEMENTS),
        }
    with postgres_db.connect() as connection:
        for statement in LINK_SCHEMA_STATEMENTS:
            connection.execute(statement)
        connection.execute(
            """INSERT INTO oap_schema_migrations(version,checksum)
               VALUES (%s,%s) ON CONFLICT (version) DO NOTHING""",
            (LINK_SCHEMA_VERSION, LINK_SCHEMA_CHECKSUM),
        )
        connection.commit()
    return {
        "dry_run": False,
        "migration": LINK_SCHEMA_VERSION,
        "checksum": LINK_SCHEMA_CHECKSUM,
        "statements": len(LINK_SCHEMA_STATEMENTS),
    }
