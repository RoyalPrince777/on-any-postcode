"""Durable owner-scoped persistence and recovery for OAP Rights Core.

Schema changes are explicit and never run at import/startup time. This store
persists canonical assets, immutable grant snapshots, decision receipts and
recovery manifests. Persistence proves read-back integrity only; it does not
prove copyright ownership, legal validity or public distribution authority.
"""
from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from datetime import datetime
from typing import Any
from uuid import UUID

from . import postgres_db, rights_core

RIGHTS_PERSISTENCE_MIGRATION_VERSION = "0020_rights_provenance_core_v1"
GENESIS_HASH = "0" * 64

SCHEMA_STATEMENTS = (
    """CREATE TABLE IF NOT EXISTS oap_rights_assets (
        asset_id UUID PRIMARY KEY,
        owner_identity_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
        kind TEXT NOT NULL,
        content_sha256 TEXT NOT NULL CHECK (length(content_sha256)=64),
        source_reference TEXT,
        parent_asset_id UUID REFERENCES oap_rights_assets(asset_id) ON DELETE RESTRICT,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE INDEX IF NOT EXISTS ix_rights_assets_owner_created
       ON oap_rights_assets(owner_identity_id,created_at DESC)""",
    """CREATE TABLE IF NOT EXISTS oap_rights_grant_snapshots (
        grant_id UUID PRIMARY KEY,
        owner_identity_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
        asset_id UUID NOT NULL REFERENCES oap_rights_assets(asset_id) ON DELETE CASCADE,
        grant_sha256 TEXT NOT NULL CHECK (length(grant_sha256)=64),
        grant_json JSONB NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE INDEX IF NOT EXISTS ix_rights_grants_owner_asset_created
       ON oap_rights_grant_snapshots(owner_identity_id,asset_id,created_at DESC)""",
    """CREATE TABLE IF NOT EXISTS oap_rights_decision_receipts (
        decision_receipt_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        owner_identity_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
        asset_id UUID NOT NULL REFERENCES oap_rights_assets(asset_id) ON DELETE CASCADE,
        decision_hash TEXT NOT NULL CHECK (length(decision_hash)=64),
        decision_json JSONB NOT NULL,
        previous_receipt_hash TEXT NOT NULL CHECK (length(previous_receipt_hash)=64),
        receipt_hash TEXT NOT NULL UNIQUE CHECK (length(receipt_hash)=64),
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE INDEX IF NOT EXISTS ix_rights_decisions_owner_asset_created
       ON oap_rights_decision_receipts(owner_identity_id,asset_id,created_at,decision_receipt_id)""",
    """CREATE TABLE IF NOT EXISTS oap_rights_recovery_manifests (
        manifest_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        owner_identity_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
        asset_id UUID NOT NULL REFERENCES oap_rights_assets(asset_id) ON DELETE CASCADE,
        manifest_sha256 TEXT NOT NULL CHECK (length(manifest_sha256)=64),
        manifest_json JSONB NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE INDEX IF NOT EXISTS ix_rights_recovery_owner_asset_created
       ON oap_rights_recovery_manifests(owner_identity_id,asset_id,created_at DESC)""",
)
SCHEMA_CHECKSUM = hashlib.sha256("\n".join(SCHEMA_STATEMENTS).encode()).hexdigest()
TABLES = frozenset({
    "oap_rights_assets",
    "oap_rights_grant_snapshots",
    "oap_rights_decision_receipts",
    "oap_rights_recovery_manifests",
})


def _uuid(value: object, field: str) -> str:
    try:
        return str(UUID(str(value)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError(f"invalid_{field}") from exc


def _jsonable(value: object) -> object:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Mapping):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set, frozenset)):
        return [_jsonable(v) for v in value]
    return value


def canonical_json_bytes(payload: object) -> bytes:
    if not isinstance(payload, Mapping):
        raise TypeError("invalid_rights_payload")
    return json.dumps(
        _jsonable(payload),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def payload_digest(payload: object) -> str:
    return hashlib.sha256(canonical_json_bytes(payload)).hexdigest()


def verify_decision(decision: object) -> dict[str, object]:
    if not isinstance(decision, Mapping):
        return {"verified": False, "decision_hash": None}
    claimed = decision.get("decision_hash")
    if not isinstance(claimed, str) or len(claimed) != 64:
        return {"verified": False, "decision_hash": None}
    body = {k: v for k, v in decision.items() if k != "decision_hash"}
    actual = payload_digest(body)
    return {"verified": actual == claimed, "decision_hash": actual}


def decision_receipt_hash(
    *,
    owner_identity_id: object,
    asset_id: object,
    decision_hash: object,
    previous_receipt_hash: object = GENESIS_HASH,
) -> str:
    owner = _uuid(owner_identity_id, "owner_identity_id")
    asset = _uuid(asset_id, "asset_id")
    if not isinstance(decision_hash, str) or len(decision_hash) != 64:
        raise ValueError("invalid_decision_hash")
    if not isinstance(previous_receipt_hash, str) or len(previous_receipt_hash) != 64:
        raise ValueError("invalid_previous_receipt_hash")
    return payload_digest({
        "owner_identity_id": owner,
        "asset_id": asset,
        "decision_hash": decision_hash,
        "previous_receipt_hash": previous_receipt_hash,
    })


def verify_recovery_manifest(payload: object, claimed_sha256: object) -> dict[str, object]:
    if not isinstance(claimed_sha256, str) or len(claimed_sha256) != 64:
        return {"verified": False, "manifest_sha256": None}
    actual = payload_digest(payload)
    return {"verified": actual == claimed_sha256, "manifest_sha256": actual}


def schema_status() -> dict[str, Any]:
    result = {
        "migration": RIGHTS_PERSISTENCE_MIGRATION_VERSION,
        "checksum": SCHEMA_CHECKSUM,
        "schema_ready": False,
        "tables": 0,
        "expected_tables": len(TABLES),
        "error": None,
    }
    base = postgres_db.postgres_status()
    if not base.get("initialized"):
        result["error"] = "base_postgres_not_ready"
        return result
    try:
        with postgres_db.connect(readonly=True) as connection:
            rows = connection.execute(
                "SELECT table_name FROM information_schema.tables WHERE table_schema='public'"
            ).fetchall()
            tables = {str(row[0]) for row in rows}
            result["tables"] = len(TABLES & tables)
            if not TABLES <= tables:
                result["error"] = "rights_persistence_schema_pending"
                return result
            migration = connection.execute(
                "SELECT checksum FROM oap_schema_migrations WHERE version=%s",
                (RIGHTS_PERSISTENCE_MIGRATION_VERSION,),
            ).fetchone()
            if migration is None or str(migration[0]) != SCHEMA_CHECKSUM:
                result["error"] = "rights_persistence_migration_not_verified"
                return result
        result["schema_ready"] = True
        return result
    except Exception:  # noqa: BLE001
        result["error"] = "rights_persistence_store_unavailable"
        return result


def init_schema(*, assume_yes: bool = False, dry_run: bool = False) -> dict[str, Any]:
    """Apply Rights persistence only after explicit Human Authority approval."""
    if not assume_yes:
        raise RuntimeError("Explicit human approval required: pass --yes")
    if dry_run:
        return {
            "dry_run": True,
            "migration": RIGHTS_PERSISTENCE_MIGRATION_VERSION,
            "checksum": SCHEMA_CHECKSUM,
            "tables": len(TABLES),
        }
    with postgres_db.connect() as connection:
        connection.execute("SELECT pg_advisory_xact_lock(%s)", (25800020,))
        row = connection.execute(
            "SELECT checksum FROM oap_schema_migrations WHERE version=%s",
            (RIGHTS_PERSISTENCE_MIGRATION_VERSION,),
        ).fetchone()
        if row is not None and str(row[0]) != SCHEMA_CHECKSUM:
            raise RuntimeError("Applied Rights persistence migration checksum mismatch")
        if row is None:
            for statement in SCHEMA_STATEMENTS:
                connection.execute(statement)
            connection.execute(
                "INSERT INTO oap_schema_migrations(version,checksum) VALUES (%s,%s)",
                (RIGHTS_PERSISTENCE_MIGRATION_VERSION, SCHEMA_CHECKSUM),
            )
        connection.commit()
    return schema_status()


class RightsStore:
    """Owner-scoped persistence; no publication or external execution authority."""

    def register_asset(self, asset: object) -> dict[str, object]:
        canonical = rights_core.canonical_asset(asset)
        with postgres_db.connect() as connection:
            row = connection.execute(
                """INSERT INTO oap_rights_assets(
                       asset_id,owner_identity_id,kind,content_sha256,
                       source_reference,parent_asset_id)
                   VALUES (%s,%s,%s,%s,%s,%s)
                   ON CONFLICT (asset_id) DO UPDATE SET
                     kind=EXCLUDED.kind,
                     content_sha256=EXCLUDED.content_sha256,
                     source_reference=EXCLUDED.source_reference,
                     parent_asset_id=EXCLUDED.parent_asset_id
                   WHERE oap_rights_assets.owner_identity_id=EXCLUDED.owner_identity_id
                   RETURNING asset_id,owner_identity_id""",
                (
                    canonical["asset_id"],
                    canonical["owner_identity_id"],
                    canonical["kind"],
                    canonical["content_sha256"],
                    canonical["source_reference"],
                    canonical["parent_asset_id"],
                ),
            ).fetchone()
            if row is None:
                raise PermissionError("rights_asset_owner_mismatch")
            connection.commit()
        return {
            "asset_id": str(row[0]),
            "owner_identity_id": str(row[1]),
            "persisted": True,
            "public_action_enabled": False,
        }

    def append_grant(self, *, owner_identity_id: object, grant: object) -> dict[str, object]:
        owner = _uuid(owner_identity_id, "owner_identity_id")
        canonical = rights_core.canonical_grant(grant)
        if canonical["owner_identity_id"] != owner:
            raise PermissionError("rights_grant_owner_mismatch")
        raw = canonical_json_bytes(canonical)
        digest = hashlib.sha256(raw).hexdigest()
        with postgres_db.connect() as connection:
            owned = connection.execute(
                """SELECT 1 FROM oap_rights_assets
                   WHERE asset_id=%s AND owner_identity_id=%s FOR UPDATE""",
                (canonical["asset_id"], owner),
            ).fetchone()
            if owned is None:
                raise PermissionError("rights_asset_not_owned")
            row = connection.execute(
                """INSERT INTO oap_rights_grant_snapshots(
                       grant_id,owner_identity_id,asset_id,grant_sha256,grant_json)
                   VALUES (%s,%s,%s,%s,%s::jsonb)
                   ON CONFLICT (grant_id) DO NOTHING
                   RETURNING grant_id""",
                (
                    canonical["grant_id"],
                    owner,
                    canonical["asset_id"],
                    digest,
                    raw.decode("utf-8"),
                ),
            ).fetchone()
            if row is None:
                raise ValueError("rights_grant_already_persisted")
            connection.commit()
        return {
            "grant_id": str(row[0]),
            "asset_id": canonical["asset_id"],
            "grant_sha256": digest,
            "persisted": True,
            "public_action_enabled": False,
        }

    def append_decision(
        self, *, owner_identity_id: object, decision: object
    ) -> dict[str, object]:
        owner = _uuid(owner_identity_id, "owner_identity_id")
        check = verify_decision(decision)
        if not check["verified"] or not isinstance(decision, Mapping):
            raise ValueError("rights_decision_integrity_failed")
        asset = _uuid(decision.get("asset_id"), "asset_id")
        requester = _uuid(decision.get("requester_identity_id"), "requester_identity_id")
        if requester != owner:
            raise PermissionError("rights_decision_owner_mismatch")
        raw = canonical_json_bytes(decision)
        with postgres_db.connect() as connection:
            owned = connection.execute(
                """SELECT 1 FROM oap_rights_assets
                   WHERE asset_id=%s AND owner_identity_id=%s FOR UPDATE""",
                (asset, owner),
            ).fetchone()
            if owned is None:
                raise PermissionError("rights_asset_not_owned")
            previous_row = connection.execute(
                """SELECT receipt_hash FROM oap_rights_decision_receipts
                   WHERE owner_identity_id=%s AND asset_id=%s
                   ORDER BY created_at DESC,decision_receipt_id DESC
                   LIMIT 1 FOR UPDATE""",
                (owner, asset),
            ).fetchone()
            previous = str(previous_row[0]) if previous_row else GENESIS_HASH
            receipt_hash = decision_receipt_hash(
                owner_identity_id=owner,
                asset_id=asset,
                decision_hash=str(check["decision_hash"]),
                previous_receipt_hash=previous,
            )
            row = connection.execute(
                """INSERT INTO oap_rights_decision_receipts(
                       owner_identity_id,asset_id,decision_hash,decision_json,
                       previous_receipt_hash,receipt_hash)
                   VALUES (%s,%s,%s,%s::jsonb,%s,%s)
                   RETURNING decision_receipt_id,created_at""",
                (
                    owner,
                    asset,
                    check["decision_hash"],
                    raw.decode("utf-8"),
                    previous,
                    receipt_hash,
                ),
            ).fetchone()
            connection.commit()
        return {
            "decision_receipt_id": str(row[0]),
            "asset_id": asset,
            "decision_hash": str(check["decision_hash"]),
            "receipt_hash": receipt_hash,
            "created_at": row[1].isoformat(),
            "persisted": True,
            "public_action_enabled": False,
        }

    def read_decisions(
        self, *, owner_identity_id: object, asset_id: object
    ) -> dict[str, object]:
        owner = _uuid(owner_identity_id, "owner_identity_id")
        asset = _uuid(asset_id, "asset_id")
        with postgres_db.connect(readonly=True) as connection:
            rows = connection.execute(
                """SELECT decision_receipt_id,decision_hash,decision_json,
                          previous_receipt_hash,receipt_hash,created_at
                   FROM oap_rights_decision_receipts
                   WHERE owner_identity_id=%s AND asset_id=%s
                   ORDER BY created_at,decision_receipt_id""",
                (owner, asset),
            ).fetchall()
        previous = GENESIS_HASH
        items = []
        verified = True
        for row in rows:
            decision = row[2]
            decision_check = verify_decision(decision)
            expected_receipt = decision_receipt_hash(
                owner_identity_id=owner,
                asset_id=asset,
                decision_hash=str(row[1]),
                previous_receipt_hash=str(row[3]),
            )
            row_ok = bool(
                decision_check["verified"]
                and str(row[3]) == previous
                and expected_receipt == str(row[4])
            )
            verified = verified and row_ok
            previous = str(row[4])
            items.append({
                "decision_receipt_id": str(row[0]),
                "decision_hash": str(row[1]),
                "receipt_hash": str(row[4]),
                "created_at": row[5].isoformat(),
                "readback_verified": row_ok,
            })
        return {
            "asset_id": asset,
            "owner_identity_id": owner,
            "receipt_count": len(items),
            "chain_verified": verified,
            "head_hash": previous if items else GENESIS_HASH,
            "items": items,
            "public_action_enabled": False,
        }

    def capture_recovery(
        self, *, owner_identity_id: object, asset_id: object, payload: object
    ) -> dict[str, object]:
        owner = _uuid(owner_identity_id, "owner_identity_id")
        asset = _uuid(asset_id, "asset_id")
        raw = canonical_json_bytes(payload)
        if len(raw) > 2_000_000:
            raise ValueError("rights_recovery_manifest_too_large")
        digest = hashlib.sha256(raw).hexdigest()
        with postgres_db.connect() as connection:
            owned = connection.execute(
                """SELECT 1 FROM oap_rights_assets
                   WHERE asset_id=%s AND owner_identity_id=%s FOR UPDATE""",
                (asset, owner),
            ).fetchone()
            if owned is None:
                raise PermissionError("rights_asset_not_owned")
            row = connection.execute(
                """INSERT INTO oap_rights_recovery_manifests(
                       owner_identity_id,asset_id,manifest_sha256,manifest_json)
                   VALUES (%s,%s,%s,%s::jsonb)
                   RETURNING manifest_id,created_at""",
                (owner, asset, digest, raw.decode("utf-8")),
            ).fetchone()
            connection.commit()
        return {
            "manifest_id": str(row[0]),
            "asset_id": asset,
            "manifest_sha256": digest,
            "created_at": row[1].isoformat(),
            "restore_performed": False,
        }

    def read_recovery(
        self, *, owner_identity_id: object, manifest_id: object
    ) -> dict[str, object]:
        owner = _uuid(owner_identity_id, "owner_identity_id")
        manifest = _uuid(manifest_id, "manifest_id")
        with postgres_db.connect(readonly=True) as connection:
            row = connection.execute(
                """SELECT asset_id,manifest_sha256,manifest_json,created_at
                   FROM oap_rights_recovery_manifests
                   WHERE manifest_id=%s AND owner_identity_id=%s""",
                (manifest, owner),
            ).fetchone()
        if row is None:
            raise PermissionError("rights_recovery_manifest_not_owned")
        check = verify_recovery_manifest(row[2], str(row[1]))
        return {
            "manifest_id": manifest,
            "asset_id": str(row[0]),
            "manifest_sha256": str(row[1]),
            "created_at": row[3].isoformat(),
            "readback_verified": bool(check["verified"]),
            "restore_performed": False,
            "public_action_enabled": False,
        }


def status() -> dict[str, object]:
    schema = schema_status()
    return {
        "component": "OAP Rights persistence",
        "schema_ready": bool(schema["schema_ready"]),
        "asset_persistence_defined": True,
        "grant_snapshot_persistence_defined": True,
        "decision_receipt_chain_defined": True,
        "recovery_manifest_defined": True,
        "migration_applied": bool(schema["schema_ready"]),
        "public_action_enabled": False,
        "legal_validity_verified": False,
        "human_authority_final": True,
    }
