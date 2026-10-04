"""Durable OAP Commerce delivery destinations.

Owns the minimum first-party delivery data required to hand an authorised Market
order to a fulfilment provider. This module records destination data only; it
does not submit orders, capture payments, or dispatch carriers.
"""
from __future__ import annotations

import hashlib
from typing import Any
from uuid import UUID

from . import postgres_db

DELIVERY_DESTINATION_MIGRATION_VERSION = "0008_commerce_delivery_destination"

DELIVERY_DESTINATION_SCHEMA_STATEMENTS = (
    """CREATE TABLE IF NOT EXISTS oap_commerce_delivery_destinations (
        destination_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        order_id UUID NOT NULL UNIQUE
            REFERENCES oap_commerce_orders(order_id) ON DELETE CASCADE,
        buyer_identity_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
        recipient_name TEXT NOT NULL,
        address_line1 TEXT NOT NULL,
        address_line2 TEXT,
        locality TEXT NOT NULL,
        region TEXT,
        postal_code TEXT NOT NULL,
        country_code TEXT NOT NULL CHECK (char_length(country_code)=2),
        delivery_instructions TEXT,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP)""",
    """CREATE INDEX IF NOT EXISTS ix_commerce_delivery_destination_buyer
        ON oap_commerce_delivery_destinations(buyer_identity_id, updated_at DESC)""",
)

DELIVERY_DESTINATION_MIGRATION_CHECKSUM = hashlib.sha256(
    "\n".join(DELIVERY_DESTINATION_SCHEMA_STATEMENTS).encode()
).hexdigest()


def _uuid(value: object, name: str) -> str:
    try:
        return str(UUID(str(value)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError(f"invalid_{name}") from exc


def _text(
    value: object,
    *,
    name: str,
    maximum: int,
    required: bool = True,
) -> str | None:
    text = " ".join(str(value or "").strip().split())
    if required and not text:
        raise ValueError(f"{name}_required")
    if len(text) > maximum:
        raise ValueError(f"{name}_too_long")
    return text or None


def normalize_destination(
    *,
    recipient_name: object,
    address_line1: object,
    address_line2: object = "",
    locality: object,
    region: object = "",
    postal_code: object,
    country_code: object,
    delivery_instructions: object = "",
) -> dict[str, str | None]:
    country = str(country_code or "").strip().upper()
    if len(country) != 2 or not country.isalpha():
        raise ValueError("invalid_country_code")
    return {
        "recipient_name": _text(recipient_name, name="recipient_name", maximum=160),
        "address_line1": _text(address_line1, name="address_line1", maximum=240),
        "address_line2": _text(
            address_line2, name="address_line2", maximum=240, required=False
        ),
        "locality": _text(locality, name="locality", maximum=160),
        "region": _text(region, name="region", maximum=160, required=False),
        "postal_code": _text(postal_code, name="postal_code", maximum=32),
        "country_code": country,
        "delivery_instructions": _text(
            delivery_instructions,
            name="delivery_instructions",
            maximum=500,
            required=False,
        ),
    }


def init_schema(*, assume_yes: bool = False, dry_run: bool = True) -> dict[str, object]:
    if not assume_yes:
        raise RuntimeError("Explicit human approval required: pass --yes")
    if dry_run:
        return {
            "dry_run": True,
            "migration": DELIVERY_DESTINATION_MIGRATION_VERSION,
            "checksum": DELIVERY_DESTINATION_MIGRATION_CHECKSUM,
            "schema_ready": False,
        }
    with postgres_db.connect() as connection:
        connection.execute("SELECT pg_advisory_xact_lock(%s)", (25800008,))
        existing = connection.execute(
            "SELECT checksum FROM oap_schema_migrations WHERE version=%s",
            (DELIVERY_DESTINATION_MIGRATION_VERSION,),
        ).fetchone()
        if existing is not None and str(existing[0]) != DELIVERY_DESTINATION_MIGRATION_CHECKSUM:
            raise RuntimeError("Applied delivery-destination migration checksum mismatch")
        if existing is None:
            for statement in DELIVERY_DESTINATION_SCHEMA_STATEMENTS:
                connection.execute(statement)
            connection.execute(
                "INSERT INTO oap_schema_migrations(version,checksum) VALUES (%s,%s)",
                (
                    DELIVERY_DESTINATION_MIGRATION_VERSION,
                    DELIVERY_DESTINATION_MIGRATION_CHECKSUM,
                ),
            )
        connection.commit()
    return schema_status()


def schema_status() -> dict[str, object]:
    result: dict[str, object] = {
        "migration": DELIVERY_DESTINATION_MIGRATION_VERSION,
        "checksum": DELIVERY_DESTINATION_MIGRATION_CHECKSUM,
        "schema_ready": False,
        "error": None,
    }
    try:
        with postgres_db.connect(readonly=True) as connection:
            table = connection.execute(
                "SELECT to_regclass('public.oap_commerce_delivery_destinations')"
            ).fetchone()
            if table is None or table[0] is None:
                result["error"] = "delivery_destination_schema_pending"
                return result
            row = connection.execute(
                "SELECT checksum FROM oap_schema_migrations WHERE version=%s",
                (DELIVERY_DESTINATION_MIGRATION_VERSION,),
            ).fetchone()
            if row is None or str(row[0]) != DELIVERY_DESTINATION_MIGRATION_CHECKSUM:
                result["error"] = "delivery_destination_migration_not_verified"
                return result
            result["schema_ready"] = True
            return result
    except Exception:
        result["error"] = "delivery_destination_store_unavailable"
        return result


class DeliveryDestinationStore:
    def upsert_for_order(
        self,
        *,
        buyer_identity_id: object,
        order_id: object,
        recipient_name: object,
        address_line1: object,
        locality: object,
        postal_code: object,
        country_code: object,
        address_line2: object = "",
        region: object = "",
        delivery_instructions: object = "",
    ) -> dict[str, Any]:
        buyer = _uuid(buyer_identity_id, "buyer_identity_id")
        order = _uuid(order_id, "order_id")
        destination = normalize_destination(
            recipient_name=recipient_name,
            address_line1=address_line1,
            address_line2=address_line2,
            locality=locality,
            region=region,
            postal_code=postal_code,
            country_code=country_code,
            delivery_instructions=delivery_instructions,
        )
        with postgres_db.connect() as connection:
            owned = connection.execute(
                """SELECT 1 FROM oap_commerce_orders
                   WHERE order_id=%s AND buyer_identity_id=%s
                   FOR UPDATE""",
                (order, buyer),
            ).fetchone()
            if owned is None:
                raise PermissionError("order_not_owned")
            row = connection.execute(
                """INSERT INTO oap_commerce_delivery_destinations(
                       order_id,buyer_identity_id,recipient_name,address_line1,
                       address_line2,locality,region,postal_code,country_code,
                       delivery_instructions)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                   ON CONFLICT (order_id) DO UPDATE SET
                       recipient_name=EXCLUDED.recipient_name,
                       address_line1=EXCLUDED.address_line1,
                       address_line2=EXCLUDED.address_line2,
                       locality=EXCLUDED.locality,
                       region=EXCLUDED.region,
                       postal_code=EXCLUDED.postal_code,
                       country_code=EXCLUDED.country_code,
                       delivery_instructions=EXCLUDED.delivery_instructions,
                       updated_at=CURRENT_TIMESTAMP
                   WHERE oap_commerce_delivery_destinations.buyer_identity_id=
                         EXCLUDED.buyer_identity_id
                   RETURNING destination_id,order_id,recipient_name,address_line1,
                             address_line2,locality,region,postal_code,country_code,
                             delivery_instructions,updated_at""",
                (
                    order,
                    buyer,
                    destination["recipient_name"],
                    destination["address_line1"],
                    destination["address_line2"],
                    destination["locality"],
                    destination["region"],
                    destination["postal_code"],
                    destination["country_code"],
                    destination["delivery_instructions"],
                ),
            ).fetchone()
            if row is None:
                raise PermissionError("destination_owner_mismatch")
            connection.commit()
        return {
            "destination_id": str(row[0]),
            "order_id": str(row[1]),
            "recipient_name": str(row[2]),
            "address_line1": str(row[3]),
            "address_line2": str(row[4]) if row[4] else None,
            "locality": str(row[5]),
            "region": str(row[6]) if row[6] else None,
            "postal_code": str(row[7]),
            "country_code": str(row[8]),
            "delivery_instructions": str(row[9]) if row[9] else None,
            "updated_at": row[10].isoformat(),
            "external_submission_performed": False,
            "human_authority_final": True,
        }


def status() -> dict[str, object]:
    return {
        "component": "OAP Commerce Delivery Destination",
        "schema": schema_status(),
        "one_destination_per_order": True,
        "buyer_ownership_enforced": True,
        "provider_submission_performed": False,
        "payment_capture_performed": False,
        "carrier_dispatch_performed": False,
        "human_authority_final": True,
    }
