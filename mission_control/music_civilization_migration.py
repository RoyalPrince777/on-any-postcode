"""Governed idempotent schema migration for OAP Music Civilization 0007-0012."""
from __future__ import annotations

import hashlib
import os

from . import (
    live_music_core,
    music_acceptance,
    music_accounting,
    music_assets,
    music_content_links,
    music_engagement,
    music_entitlements,
    music_evidence,
    music_purchases,
    music_recovery,
    music_rights_store,
    postgres_db,
    product_cores,
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
    (music_assets.MUSIC_ASSET_MIGRATION_VERSION, music_assets.SCHEMA_STATEMENTS),
    (music_rights_store.MUSIC_RIGHTS_MIGRATION_VERSION, music_rights_store.SCHEMA_STATEMENTS),
    (music_entitlements.MUSIC_ENTITLEMENT_MIGRATION_VERSION, music_entitlements.SCHEMA_STATEMENTS),
    (radio_core.RADIO_ALWAYS_ON_MIGRATION_VERSION, radio_core.RADIO_ALWAYS_ON_SCHEMA_STATEMENTS),
    (radio_core.RADIO_FOUNDER_APPROVAL_MIGRATION_VERSION, radio_core.RADIO_FOUNDER_APPROVAL_SCHEMA_STATEMENTS),
    (radio_core.RADIO_DELIVERY_ADMISSION_MIGRATION_VERSION, radio_core.RADIO_DELIVERY_ADMISSION_SCHEMA_STATEMENTS),
    (music_purchases.MUSIC_PURCHASE_MIGRATION_VERSION, music_purchases.SCHEMA_STATEMENTS),
    (music_accounting.MUSIC_ACCOUNTING_MIGRATION_VERSION, music_accounting.SCHEMA_STATEMENTS),
    (music_content_links.MUSIC_CONTENT_LINK_MIGRATION_VERSION, music_content_links.SCHEMA_STATEMENTS),
    (music_engagement.MUSIC_ENGAGEMENT_MIGRATION_VERSION, music_engagement.SCHEMA_STATEMENTS),
    (music_engagement.PLAYBACK_SESSION_MIGRATION_VERSION, music_engagement.PLAYBACK_SESSION_SCHEMA_STATEMENTS),
)
_LOCK_KEY = 25800012


def _checksum(statements: tuple[str, ...]) -> str:
    return hashlib.sha256("\n".join(statements).encode()).hexdigest()



def inspect() -> dict[str, object]:
    """Read-only Music migration inventory; never grants migration approval.

    Missing migration registry fails closed. Checksum drift must be reconciled
    before any separately approved application or release.
    """
    versions = [
        product_cores.PRODUCT_CORE_MIGRATION_VERSION,
        *(version for version, _ in _MIGRATIONS),
    ]
    with postgres_db.connect(readonly=True) as connection:
        registry = connection.execute(
            "SELECT to_regclass('oap_schema_migrations')"
        ).fetchone()
        if registry is None or registry[0] is None:
            return {
                "registry_present": False,
                "base_product_core_present": False,
                "existing": [],
                "pending": versions,
                "checksum_mismatches": [],
                "schema_inventory_ready": False,
                "migration_performed": False,
                "human_approval_granted": False,
            }
        rows = connection.execute(
            "SELECT version,checksum FROM oap_schema_migrations WHERE version=ANY(%s)",
            (versions,),
        ).fetchall()
    known = {str(version): str(checksum) for version, checksum in rows}
    existing: list[str] = []
    pending: list[str] = []
    mismatches: list[str] = []
    for version, statements in _MIGRATIONS:
        stored = known.get(version)
        if stored is None:
            pending.append(version)
        elif stored != _checksum(statements):
            mismatches.append(version)
        else:
            existing.append(version)
    base_present = product_cores.PRODUCT_CORE_MIGRATION_VERSION in known
    if not base_present:
        pending.insert(0, product_cores.PRODUCT_CORE_MIGRATION_VERSION)
    return {
        "registry_present": True,
        "base_product_core_present": base_present,
        "existing": existing,
        "pending": pending,
        "checksum_mismatches": mismatches,
        "schema_inventory_ready": base_present and not pending and not mismatches,
        "base_checksum_not_evaluated": True,
        "migration_performed": False,
        "human_approval_granted": False,
    }


def apply(*, assume_yes: bool = False) -> dict[str, object]:
    if not assume_yes:
        raise RuntimeError("Explicit human approval required")
    base_result = product_cores.init_product_core_schema(assume_yes=True)
    if not base_result.get("schema_ready"):
        raise RuntimeError("Base Product Core migration 0006 not ready")
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
        "base_product_core_ready": True,
        "base_product_core_migration": product_cores.PRODUCT_CORE_MIGRATION_VERSION,
        "applied": applied,
        "existing": existing,
        "versions": [version for version, _ in _MIGRATIONS],
        "schema_ready": True,
    }


def apply_from_environment() -> dict[str, object] | None:
    if os.environ.get("OAP_MUSIC_SCHEMA_AUTO_APPLY") != "1":
        return None
    return apply(assume_yes=True)
