"""Staged OAP-owned Fashion persistence, never initialized at import time.

FASHION_SCHEMA_STATEMENTS are a proposed *new*, explicit migration only.
Never modify existing Market, Commerce, or Product Core migrations.
No supplier, publication, payment, order, or deployment execution.
"""
from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping

from . import certification, postgres_db, product_cores
from .fashion_first_party import FashionDraft, FashionError, identity
from .fashion_snapshot import restore, snapshot

FASHION_MIGRATION_VERSION = "0007_first_party_fashion"
FASHION_SCHEMA_STATEMENTS = (
    """CREATE TABLE IF NOT EXISTS oap_fashion_snapshots (
        product_id UUID PRIMARY KEY REFERENCES products(id) ON DELETE RESTRICT,
        owner_identity_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
        version BIGINT NOT NULL DEFAULT 1 CHECK (version >= 1),
        snapshot_json JSONB NOT NULL,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE INDEX IF NOT EXISTS ix_oap_fashion_owner
       ON oap_fashion_snapshots(owner_identity_id, updated_at DESC)""",
)



FASHION_MIGRATION_CHECKSUM = hashlib.sha256(
    json.dumps(FASHION_SCHEMA_STATEMENTS, separators=(",", ":")).encode("utf-8")
).hexdigest()


def fashion_schema_status() -> dict[str, object]:
    """Read-only verification; missing schema or altered checksum cannot be green."""
    result: dict[str, object] = {
        "migration": FASHION_MIGRATION_VERSION,
        "checksum": FASHION_MIGRATION_CHECKSUM,
        "schema_ready": False,
        "error": None,
        "live_migration_performed": False,
    }
    if not product_cores.product_core_schema_status().get("schema_ready"):
        result["error"] = "product_core_schema_not_ready"
        return result
    try:
        with postgres_db.connect(readonly=True) as connection:
            row = connection.execute(
                """SELECT table_name FROM information_schema.tables
                   WHERE table_schema='public'
                     AND table_name='oap_fashion_snapshots'"""
            ).fetchone()
            if row is None:
                result["error"] = "fashion_table_missing"
                return result
            migration = connection.execute(
                "SELECT checksum FROM oap_schema_migrations WHERE version=%s",
                (FASHION_MIGRATION_VERSION,),
            ).fetchone()
            if migration is None or str(migration[0]) != FASHION_MIGRATION_CHECKSUM:
                result["error"] = "fashion_migration_not_verified"
                return result
    except Exception:  # noqa: BLE001 - readiness must fail closed.
        result["error"] = "fashion_store_unavailable"
        return result
    result["schema_ready"] = True
    return result


def fashion_schema_dry_run() -> dict[str, object]:
    """No connection, DDL or migration. Return audit-ready schema metadata."""
    return {
        "migration": FASHION_MIGRATION_VERSION,
        "checksum": FASHION_MIGRATION_CHECKSUM,
        "statements": len(FASHION_SCHEMA_STATEMENTS),
        "dry_run": True,
        "schema_applied": False,
        "human_authority_final": True,
    }


def _encode(envelope: Mapping[str, object]) -> str:
    return json.dumps(envelope, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def read_fashion(*, actor_id: object, product_id: object) -> tuple[FashionDraft, int]:
    """Read only the owner's stored draft; fail closed on schema or data errors."""
    owner, product = identity(actor_id), identity(product_id)
    with postgres_db.connect(readonly=True) as connection:
        row = connection.execute(
            """SELECT snapshot_json,version FROM oap_fashion_snapshots
               WHERE owner_identity_id=%s AND product_id=%s""",
            (owner, product),
        ).fetchone()
    if row is None:
        raise FashionError("fashion_snapshot_not_found")
    envelope = row[0]
    if isinstance(envelope, str):
        try:
            envelope = json.loads(envelope)
        except (TypeError, ValueError) as exc:
            raise FashionError("invalid_fashion_snapshot") from exc
    if type(row[1]) is not int or row[1] < 1:
        raise FashionError("invalid_fashion_revision")
    return restore(envelope, actor_id=owner, product_id=product), row[1]


def save_fashion(
    *, actor_id: object, draft: FashionDraft, expected_revision: int
) -> int:
    """CAS write: revision 0 is create-only; positive revision is update-only.

    Recheck current OAP Certified Merchant status, never trust draft flags.
    This is not an HTTP action. A separate approved migration must exist.
    """
    owner = identity(actor_id)
    if owner != identity(draft.owner_identity_id):
        raise FashionError("not_product_owner")
    if type(expected_revision) is not int or expected_revision < 0:
        raise FashionError("invalid_fashion_revision")
    if not draft.merchant_certified:
        raise FashionError("certified_merchant_required")
    try:
        status = certification.identity_status(owner)
    except certification.CertificationUnavailable as exc:
        raise FashionError("merchant_certification_unavailable") from exc
    if status.get("merchant") is not True:
        raise FashionError("certified_merchant_required")
    envelope = snapshot(draft, actor_id=owner)
    payload = _encode({"payload": envelope["payload"], "sha256": envelope["sha256"]})
    with postgres_db.connect() as connection:
        existing_product = connection.execute(
            """SELECT 1 FROM products
               WHERE id=%s AND seller_id=%s FOR SHARE""",
            (draft.product_id, owner),
        ).fetchone()
        if existing_product is None:
            raise FashionError("owned_market_product_not_found")
        if expected_revision == 0:
            row = connection.execute(
                """INSERT INTO oap_fashion_snapshots
                   (product_id,owner_identity_id,version,snapshot_json)
                   VALUES (%s,%s,1,%s::jsonb)
                   ON CONFLICT (product_id) DO NOTHING
                   RETURNING version""",
                (draft.product_id, owner, payload),
            ).fetchone()
        else:
            row = connection.execute(
                """UPDATE oap_fashion_snapshots SET
                   snapshot_json=%s::jsonb,version=version+1,
                   updated_at=CURRENT_TIMESTAMP
                   WHERE product_id=%s AND owner_identity_id=%s
                     AND version=%s RETURNING version""",
                (payload, draft.product_id, owner, expected_revision),
            ).fetchone()
        if row is None:
            raise FashionError("fashion_revision_conflict")
        connection.commit()
        return int(row[0])
