"""Governed OAP Library ebook schema install and read-back proof.

This module only creates the reviewed first-party Library tables/indexes.
It creates no users, books, products, payments, provider receipts, entitlements,
or ownership rows.
"""
from __future__ import annotations

import hashlib

from . import (
    oap_book_entitlements,
    oap_ebook_catalogue_store,
    oap_ebook_creator_store,
    oap_ebook_market,
    postgres_db,
)

MIGRATION_VERSION = "oap_library_ebook_runtime_v1"
_REQUIRED_TABLES = (
    "oap_ebook_editions",
    "oap_book_entitlements",
    "oap_ebook_creator_drafts",
    "oap_ebook_market_products",
)
_PREREQUISITES = (
    "users",
    "products",
    "oap_commerce_orders",
    "oap_commerce_order_items",
    "oap_commerce_payment_intents",
    "oap_commerce_provider_receipts",
)
_STATEMENTS = (
    *oap_ebook_catalogue_store.CATALOGUE_SCHEMA_SQL,
    *oap_book_entitlements.SCHEMA_SQL,
    *oap_ebook_creator_store.SCHEMA_STATEMENTS,
    *oap_ebook_market.SCHEMA_STATEMENTS,
)
MIGRATION_CHECKSUM = hashlib.sha256("\n".join(_STATEMENTS).encode()).hexdigest()


class LibraryEbookSchemaUnavailable(RuntimeError):
    pass


def _regclass(connection, name: str) -> bool:
    row = connection.execute("SELECT to_regclass(%s)", (f"public.{name}",)).fetchone()
    return bool(row and row[0])


def readback() -> dict[str, object]:
    """Read only schema presence; never inspect member or payment rows."""
    try:
        with postgres_db.connect(readonly=True) as connection:
            prerequisites = {name: _regclass(connection, name) for name in _PREREQUISITES}
            tables = {name: _regclass(connection, name) for name in _REQUIRED_TABLES}
    except Exception as exc:
        raise LibraryEbookSchemaUnavailable("library_ebook_schema_readback_failed") from exc
    return {
        "migration": MIGRATION_VERSION,
        "checksum": MIGRATION_CHECKSUM,
        "prerequisites": prerequisites,
        "tables": tables,
        "prerequisites_ready": all(prerequisites.values()),
        "schema_ready": all(tables.values()),
        "member_rows_read": False,
        "payment_rows_read": False,
        "payment_capture_performed": False,
        "ownership_created": False,
    }


def install(*, assume_yes: bool = False, dry_run: bool = False) -> dict[str, object]:
    if not assume_yes:
        raise RuntimeError("explicit_confirmation_required")
    if dry_run:
        return {
            "migration": MIGRATION_VERSION,
            "checksum": MIGRATION_CHECKSUM,
            "schema_ready": False,
            "dry_run": True,
            "statement_count": len(_STATEMENTS),
            "payment_capture_performed": False,
            "ownership_created": False,
        }

    try:
        with postgres_db.connect() as connection:
            missing = [
                name for name in _PREREQUISITES if not _regclass(connection, name)
            ]
            if missing:
                raise LibraryEbookSchemaUnavailable(
                    "library_ebook_schema_prerequisites_missing:" + ",".join(missing)
                )
            for statement in _STATEMENTS:
                connection.execute(statement)
            connection.commit()
    except LibraryEbookSchemaUnavailable:
        raise
    except Exception as exc:
        raise LibraryEbookSchemaUnavailable("library_ebook_schema_install_failed") from exc

    proof = readback()
    if proof["schema_ready"] is not True:
        raise LibraryEbookSchemaUnavailable("library_ebook_schema_readback_incomplete")
    return {
        **proof,
        "dry_run": False,
        "statement_count": len(_STATEMENTS),
    }
