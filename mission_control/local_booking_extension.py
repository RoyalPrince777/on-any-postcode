"""Additive barber supply extension to the existing OAP Direct event/booking spine.

The original 0007 supply-core schema and checksum must never be rewritten.
This only permits properly onboarded personal-service suppliers and barber
listings. No supplier, availability slot, price, booking or payment is seeded.
"""
from __future__ import annotations

import hashlib

from . import postgres_db, travel_supply_core

BARBER_EXTENSION_MIGRATION_VERSION = "20261025_oap_direct_barber_v1"
BARBER_EXTENSION_STATEMENTS = (
    "ALTER TABLE oap_supply_listings "
    "DROP CONSTRAINT oap_supply_listings_category_check",
    """ALTER TABLE oap_supply_listings
       ADD CONSTRAINT oap_supply_listings_category_check
       CHECK (category IN ('stay','attraction','activity','car_rental',
                          'transport','event','barber'))""",
    "ALTER TABLE oap_supply_suppliers "
    "DROP CONSTRAINT oap_supply_suppliers_supplier_type_check",
    """ALTER TABLE oap_supply_suppliers
       ADD CONSTRAINT oap_supply_suppliers_supplier_type_check
       CHECK (supplier_type IN ('accommodation','experience','mobility',
                               'venue','mixed','personal_service'))""",
)
BARBER_EXTENSION_CHECKSUM = hashlib.sha256(
    "\n".join(BARBER_EXTENSION_STATEMENTS).encode()
).hexdigest()

_EXPECTED_CONSTRAINTS = (
    ("oap_supply_listings", "oap_supply_listings_category_check", "category"),
    (
        "oap_supply_suppliers",
        "oap_supply_suppliers_supplier_type_check",
        "supplier_type",
    ),
)


def schema_status() -> dict[str, object]:
    """Treat absent, stale and mismatched migration receipts as unready."""

    base = travel_supply_core.supply_core_schema_status()
    result: dict[str, object] = {
        "component": "OAP Direct Barber Extension",
        "migration": BARBER_EXTENSION_MIGRATION_VERSION,
        "checksum": BARBER_EXTENSION_CHECKSUM,
        "schema_ready": False,
        "barber_supplier_type": "personal_service",
        "barber_listing_category": "barber",
        "event_category_preserved": True,
        "requires_certified_supplier": True,
        "requires_actual_inventory": True,
        "supplier_confirmation_required": True,
        "payment_enabled": False,
        "trial_started": False,
        "founder_final": True,
    }
    if not base.get("schema_ready"):
        result["error"] = "supply_core_not_ready"
        return result
    try:
        with postgres_db.connect(readonly=True) as connection:
            row = connection.execute(
                "SELECT checksum FROM oap_schema_migrations WHERE version=%s",
                (BARBER_EXTENSION_MIGRATION_VERSION,),
            ).fetchone()
        if row is None or str(row[0]) != BARBER_EXTENSION_CHECKSUM:
            result["error"] = "barber_extension_not_verified"
            return result
        result["schema_ready"] = True
        return result
    except Exception:  # noqa: BLE001
        result["error"] = "barber_extension_store_unavailable"
        return result


def init_schema(*, assume_yes: bool = False, dry_run: bool = False) -> dict[str, object]:
    """Founder-gated atomic extension; no automatic migration on boot."""

    if not assume_yes:
        raise RuntimeError("Explicit Human Authority approval required")
    if not travel_supply_core.supply_core_schema_status().get("schema_ready"):
        raise RuntimeError("Verified OAP Direct supply core required")
    if dry_run:
        return {
            "dry_run": True,
            "migration": BARBER_EXTENSION_MIGRATION_VERSION,
            "checksum": BARBER_EXTENSION_CHECKSUM,
            "statement_count": len(BARBER_EXTENSION_STATEMENTS),
        }
    with postgres_db.connect() as connection:
        connection.execute("SELECT pg_advisory_xact_lock(%s)", (25800117,))
        receipt = connection.execute(
            "SELECT checksum FROM oap_schema_migrations WHERE version=%s",
            (BARBER_EXTENSION_MIGRATION_VERSION,),
        ).fetchone()
        if receipt is not None:
            if str(receipt[0]) != BARBER_EXTENSION_CHECKSUM:
                raise RuntimeError("Applied barber extension checksum mismatch")
            return schema_status()
        for table, constraint, column in _EXPECTED_CONSTRAINTS:
            row = connection.execute(
                """SELECT pg_get_constraintdef(c.oid)
                   FROM pg_constraint c JOIN pg_class t ON t.oid=c.conrelid
                   JOIN pg_namespace n ON n.oid=t.relnamespace
                   WHERE n.nspname=current_schema()
                     AND t.relname=%s AND c.conname=%s""",
                (table, constraint),
            ).fetchone()
            if row is None or column not in str(row[0]):
                raise RuntimeError("Existing OAP Supply Core constraint not verified")
        for statement in BARBER_EXTENSION_STATEMENTS:
            connection.execute(statement)
        connection.execute(
            "INSERT INTO oap_schema_migrations(version,checksum) VALUES (%s,%s)",
            (BARBER_EXTENSION_MIGRATION_VERSION, BARBER_EXTENSION_CHECKSUM),
        )
        connection.commit()
    return schema_status()
