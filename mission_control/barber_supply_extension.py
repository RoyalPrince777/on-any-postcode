"""Explicit additive barber booking category for OAP Direct.

This is a separate, human-approved migration. Never modify the checksum of the
already-applied OAP Supply Core migration. No supplier, slots or payments created.
"""
from __future__ import annotations

import hashlib
from typing import Any

from . import postgres_db, travel_supply_core

VERSION = "0008_oap_direct_barber_supply"
LOCK_ID = 25800008
STATEMENTS = (
    """ALTER TABLE oap_supply_suppliers
       DROP CONSTRAINT IF EXISTS oap_supply_suppliers_supplier_type_check""",
    """ALTER TABLE oap_supply_suppliers
       ADD CONSTRAINT oap_supply_suppliers_supplier_type_check
       CHECK (supplier_type IN ('accommodation','experience','mobility','venue','mixed','service'))""",
    """ALTER TABLE oap_supply_listings
       DROP CONSTRAINT IF EXISTS oap_supply_listings_category_check""",
    """ALTER TABLE oap_supply_listings
       ADD CONSTRAINT oap_supply_listings_category_check
       CHECK (category IN ('stay','attraction','activity','car_rental','transport','event','barber'))""",
)
CHECKSUM = hashlib.sha256("\n".join(STATEMENTS).encode()).hexdigest()


def status() -> dict[str, Any]:
    result = {
        "migration": VERSION,
        "schema_ready": False,
        "human_authority_required": True,
        "owner_certification_required": True,
        "real_supplier_inventory_required": True,
        "payment_execution_enabled": False,
        "money_movement": False,
    }
    if not travel_supply_core.supply_core_schema_status().get("schema_ready"):
        return result
    try:
        with postgres_db.connect(readonly=True) as connection:
            row = connection.execute(
                "SELECT checksum FROM oap_schema_migrations WHERE version=%s",
                (VERSION,),
            ).fetchone()
            if row is None or str(row[0]) != CHECKSUM:
                return result
            checks = connection.execute(
                """SELECT conname,pg_get_constraintdef(oid)
                   FROM pg_constraint
                   WHERE conrelid IN ('oap_supply_suppliers'::regclass,
                                     'oap_supply_listings'::regclass)
                     AND conname IN ('oap_supply_suppliers_supplier_type_check',
                                     'oap_supply_listings_category_check')"""
            ).fetchall()
        definitions = {str(name): str(definition) for name, definition in checks}
        result["schema_ready"] = (
            "service" in definitions.get("oap_supply_suppliers_supplier_type_check", "")
            and "barber" in definitions.get("oap_supply_listings_category_check", "")
        )
    except Exception:  # noqa: BLE001
        return result
    return result


def init_schema(*, assume_yes: bool = False, dry_run: bool = False) -> dict[str, Any]:
    if not assume_yes:
        raise RuntimeError("explicit_human_approval_required")
    if not travel_supply_core.supply_core_schema_status().get("schema_ready"):
        raise RuntimeError("base_supply_schema_not_ready")
    if dry_run:
        return {"migration": VERSION, "checksum": CHECKSUM, "dry_run": True,
                "schema_ready": False, "human_authority_final": True}
    with postgres_db.connect() as connection:
        connection.execute("SELECT pg_advisory_xact_lock(%s)", (LOCK_ID,))
        row = connection.execute(
            "SELECT checksum FROM oap_schema_migrations WHERE version=%s", (VERSION,)
        ).fetchone()
        if row is not None and str(row[0]) != CHECKSUM:
            raise RuntimeError("barber_supply_migration_checksum_mismatch")
        if row is None:
            for statement in STATEMENTS:
                connection.execute(statement)
            connection.execute(
                "INSERT INTO oap_schema_migrations(version,checksum) VALUES (%s,%s)",
                (VERSION, CHECKSUM),
            )
        connection.commit()
    return status()
