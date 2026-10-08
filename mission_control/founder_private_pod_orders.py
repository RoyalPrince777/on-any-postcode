"""Durable Founder-private POD order snapshots.

Persists provider choice, canonical OAP order truth, mapped provider payload,
and readback state so routing cannot silently drift between planning and later
execution/reconciliation.
"""
from __future__ import annotations

import hashlib
import json
import uuid
from typing import Any

from . import postgres_db

MIGRATION_VERSION = "0012_founder_private_pod_orders"
SCHEMA_STATEMENTS = (
    """CREATE TABLE IF NOT EXISTS oap_founder_private_pod_orders (
        private_order_id UUID PRIMARY KEY,
        owner_identity_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
        provider_id TEXT NOT NULL CHECK (provider_id IN ('prodigi','printful','tapstitch')),
        canonical_order JSONB NOT NULL,
        provider_payload JSONB NOT NULL,
        provider_reference TEXT NOT NULL DEFAULT '',
        provider_state TEXT NOT NULL DEFAULT 'PLANNED',
        canonical_state TEXT NOT NULL DEFAULT 'DRAFT',
        idempotency_key TEXT NOT NULL,
        recovery_required BOOLEAN NOT NULL DEFAULT FALSE,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(owner_identity_id,idempotency_key)
    )""",
    """CREATE INDEX IF NOT EXISTS ix_founder_private_pod_orders_owner
       ON oap_founder_private_pod_orders(owner_identity_id,created_at DESC)""",
    """CREATE INDEX IF NOT EXISTS ix_founder_private_pod_orders_provider_reference
       ON oap_founder_private_pod_orders(provider_id,provider_reference)
       WHERE provider_reference <> ''""",
)
MIGRATION_CHECKSUM = hashlib.sha256("\n".join(SCHEMA_STATEMENTS).encode()).hexdigest()


class FounderPrivatePodOrderUnavailable(RuntimeError):
    """Safe durable private POD order error."""


def _uuid(value: object, code: str) -> str:
    try:
        return str(uuid.UUID(str(value)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError(code) from exc


def _clean(value: object, *, limit: int) -> str:
    return str(value or "").strip()[:limit]


def _idempotency(value: object) -> str:
    key = _clean(value, limit=160)
    if len(key) < 8:
        raise ValueError("private_pod_idempotency_key_invalid")
    allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._:-")
    if any(char not in allowed for char in key):
        raise ValueError("private_pod_idempotency_key_invalid")
    return key


def _row(values) -> dict[str, Any]:
    return {
        "private_order_id": str(values[0]),
        "product_id": str(values[1]),
        "provider_id": str(values[2]),
        "canonical_order": dict(values[3] or {}),
        "provider_payload": dict(values[4] or {}),
        "provider_reference": str(values[5] or ""),
        "provider_state": str(values[6]),
        "canonical_state": str(values[7]),
        "idempotency_key": str(values[8]),
        "recovery_required": bool(values[9]),
        "created_at": values[10].isoformat(),
        "updated_at": values[11].isoformat(),
        "scope": "founder_private",
        "public_merchant_access": False,
        "human_authority_final": True,
    }


def _table_exists(connection, table_name: str) -> bool:
    row = connection.execute(
        """SELECT 1 FROM information_schema.tables
           WHERE table_schema='public' AND table_name=%s LIMIT 1""",
        (table_name,),
    ).fetchone()
    return row is not None


def schema_status() -> dict[str, object]:
    result: dict[str, object] = {
        "component": "OAP Founder Private POD Orders",
        "migration": MIGRATION_VERSION,
        "checksum": MIGRATION_CHECKSUM,
        "database_reachable": False,
        "order_table_ready": False,
        "schema_ready": False,
        "public_merchant_access": False,
        "external_execution_enabled_here": False,
        "error": None,
    }
    try:
        with postgres_db.connect(readonly=True) as connection:
            result["database_reachable"] = True
            ready = _table_exists(connection, "oap_founder_private_pod_orders")
            result["order_table_ready"] = ready
            result["schema_ready"] = ready
            if not ready:
                result["error"] = "founder_private_pod_order_schema_pending"
            return result
    except (postgres_db._driver().Error, RuntimeError, OSError):
        result["error"] = "founder_private_pod_order_schema_unavailable"
        return result


def init_schema(*, assume_yes: bool = False, dry_run: bool = False) -> dict[str, object]:
    if not assume_yes:
        raise RuntimeError("Explicit human approval required: pass --yes")
    if dry_run:
        return {
            "migration": MIGRATION_VERSION,
            "checksum": MIGRATION_CHECKSUM,
            "dry_run": True,
            "schema_ready": False,
            "public_merchant_access": False,
            "external_execution_enabled_here": False,
            "human_authority_final": True,
        }
    try:
        with postgres_db.connect() as connection:
            for statement in SCHEMA_STATEMENTS:
                connection.execute(statement)
            connection.commit()
    except Exception as exc:
        raise FounderPrivatePodOrderUnavailable(
            "private_pod_order_schema_init_failed"
        ) from exc
    result = schema_status()
    if result.get("schema_ready") is not True:
        raise FounderPrivatePodOrderUnavailable(
            "private_pod_order_schema_not_ready"
        )
    result["dry_run"] = False
    result["human_authority_final"] = True
    return result


class FounderPrivatePodOrderStore:
    def create_snapshot(
        self,
        *,
        owner_identity_id: object,
        product_id: object,
        provider_id: object,
        canonical_order: object,
        provider_payload: object,
        idempotency_key: object,
    ) -> dict[str, Any]:
        owner = _uuid(owner_identity_id, "invalid_owner_identity")
        product = _uuid(product_id, "invalid_product_id")
        provider = _clean(provider_id, limit=40).lower()
        if provider not in {"prodigi", "printful", "tapstitch"}:
            raise ValueError("private_pod_provider_invalid")
        if not isinstance(canonical_order, dict) or not isinstance(provider_payload, dict):
            raise TypeError("private_pod_order_mapping_required")
        key = _idempotency(idempotency_key)
        private_order_id = str(uuid.uuid4())
        try:
            with postgres_db.connect() as connection:
                row = connection.execute(
                    """INSERT INTO oap_founder_private_pod_orders(
                           private_order_id,owner_identity_id,product_id,provider_id,
                           canonical_order,provider_payload,idempotency_key)
                       VALUES (%s,%s,%s,%s,%s::jsonb,%s::jsonb,%s)
                       ON CONFLICT(owner_identity_id,idempotency_key) DO UPDATE
                       SET idempotency_key=EXCLUDED.idempotency_key
                       WHERE oap_founder_private_pod_orders.product_id=EXCLUDED.product_id
                         AND oap_founder_private_pod_orders.provider_id=EXCLUDED.provider_id
                       RETURNING private_order_id,product_id,provider_id,canonical_order,
                                 provider_payload,provider_reference,provider_state,
                                 canonical_state,idempotency_key,recovery_required,
                                 created_at,updated_at""",
                    (
                        private_order_id,
                        owner,
                        product,
                        provider,
                        json.dumps(canonical_order, sort_keys=True),
                        json.dumps(provider_payload, sort_keys=True),
                        key,
                    ),
                ).fetchone()
                if row is None:
                    raise ValueError("private_pod_idempotency_conflict")
                connection.commit()
        except (TypeError, ValueError):
            raise
        except Exception as exc:
            raise FounderPrivatePodOrderUnavailable(
                "private_pod_snapshot_write_failed"
            ) from exc
        return _row(row)

    def attach_provider_receipt(
        self,
        *,
        owner_identity_id: object,
        private_order_id: object,
        provider_receipt: object,
    ) -> dict[str, Any]:
        if not isinstance(provider_receipt, dict):
            raise TypeError("private_pod_provider_receipt_required")
        owner = _uuid(owner_identity_id, "invalid_owner_identity")
        private_order = _uuid(private_order_id, "invalid_private_order_id")
        reference = _clean(provider_receipt.get("provider_reference"), limit=120)
        state = _clean(provider_receipt.get("provider_state"), limit=40).upper()
        if not reference or not state:
            raise ValueError("private_pod_provider_receipt_incomplete")
        try:
            with postgres_db.connect() as connection:
                row = connection.execute(
                    """UPDATE oap_founder_private_pod_orders
                       SET provider_reference=%s,provider_state=%s,
                           updated_at=CURRENT_TIMESTAMP
                       WHERE private_order_id=%s AND owner_identity_id=%s
                       RETURNING private_order_id,product_id,provider_id,canonical_order,
                                 provider_payload,provider_reference,provider_state,
                                 canonical_state,idempotency_key,recovery_required,
                                 created_at,updated_at""",
                    (reference, state, private_order, owner),
                ).fetchone()
                if row is None:
                    raise PermissionError("private_pod_order_not_owned")
                connection.commit()
        except (PermissionError, TypeError, ValueError):
            raise
        except Exception as exc:
            raise FounderPrivatePodOrderUnavailable(
                "private_pod_provider_receipt_update_failed"
            ) from exc
        return _row(row)

    def update_readback(
        self,
        *,
        owner_identity_id: object,
        private_order_id: object,
        provider_reference: object,
        provider_state: object,
        canonical_state: object,
        recovery_required: object,
    ) -> dict[str, Any]:
        owner = _uuid(owner_identity_id, "invalid_owner_identity")
        private_order = _uuid(private_order_id, "invalid_private_order_id")
        reference = _clean(provider_reference, limit=120)
        state = _clean(provider_state, limit=40).upper()
        canonical = _clean(canonical_state, limit=40).upper()
        try:
            with postgres_db.connect() as connection:
                row = connection.execute(
                    """UPDATE oap_founder_private_pod_orders
                       SET provider_reference=%s,provider_state=%s,
                           canonical_state=%s,recovery_required=%s,
                           updated_at=CURRENT_TIMESTAMP
                       WHERE private_order_id=%s AND owner_identity_id=%s
                       RETURNING private_order_id,product_id,provider_id,canonical_order,
                                 provider_payload,provider_reference,provider_state,
                                 canonical_state,idempotency_key,recovery_required,
                                 created_at,updated_at""",
                    (
                        reference,
                        state,
                        canonical,
                        bool(recovery_required),
                        private_order,
                        owner,
                    ),
                ).fetchone()
                if row is None:
                    raise PermissionError("private_pod_order_not_owned")
                connection.commit()
        except (PermissionError, ValueError):
            raise
        except Exception as exc:
            raise FounderPrivatePodOrderUnavailable(
                "private_pod_readback_update_failed"
            ) from exc
        return _row(row)

    def read_for_owner(
        self, *, owner_identity_id: object, private_order_id: object
    ) -> dict[str, Any]:
        owner = _uuid(owner_identity_id, "invalid_owner_identity")
        private_order = _uuid(private_order_id, "invalid_private_order_id")
        try:
            with postgres_db.connect(readonly=True) as connection:
                row = connection.execute(
                    """SELECT private_order_id,product_id,provider_id,canonical_order,
                              provider_payload,provider_reference,provider_state,
                              canonical_state,idempotency_key,recovery_required,
                              created_at,updated_at
                       FROM oap_founder_private_pod_orders
                       WHERE private_order_id=%s AND owner_identity_id=%s""",
                    (private_order, owner),
                ).fetchone()
        except Exception as exc:
            raise FounderPrivatePodOrderUnavailable(
                "private_pod_order_read_failed"
            ) from exc
        if row is None:
            raise PermissionError("private_pod_order_not_owned")
        return _row(row)


STORE = FounderPrivatePodOrderStore()


def status() -> dict[str, object]:
    return {
        "system": "OAP Founder Private POD Orders",
        "migration": MIGRATION_VERSION,
        "checksum": MIGRATION_CHECKSUM,
        "durable_provider_choice": True,
        "durable_canonical_order": True,
        "durable_provider_payload": True,
        "public_merchant_access": False,
        "external_execution_enabled_here": False,
        "secret_values_persisted": False,
        "human_authority_final": True,
    }
