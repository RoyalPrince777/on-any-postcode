"""Durable redacted receipts for secure payment/POD provider execution."""
from __future__ import annotations

import hashlib
import json
import uuid
from collections.abc import Mapping

from . import postgres_db

MIGRATION_VERSION = "commerce_provider_receipts_v1"
SCHEMA_STATEMENTS = (
    """CREATE TABLE IF NOT EXISTS oap_commerce_provider_receipts (
        receipt_id UUID PRIMARY KEY,
        owner_identity_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        kind TEXT NOT NULL CHECK (kind IN ('payment','payment_webhook','payment_refund','pod','pod_webhook')),
        subject_id TEXT NOT NULL,
        provider_id TEXT NOT NULL,
        provider_reference TEXT NOT NULL,
        provider_state TEXT NOT NULL,
        idempotency_key TEXT NOT NULL,
        receipt_hash TEXT NOT NULL UNIQUE,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(kind,provider_id,idempotency_key)
    )""",
    """CREATE INDEX IF NOT EXISTS ix_commerce_provider_receipts_owner
       ON oap_commerce_provider_receipts(owner_identity_id,created_at DESC)""",
    """CREATE INDEX IF NOT EXISTS ix_commerce_provider_receipts_subject
       ON oap_commerce_provider_receipts(subject_id,created_at DESC)""",
)
MIGRATION_CHECKSUM = hashlib.sha256("\n".join(SCHEMA_STATEMENTS).encode()).hexdigest()


class CommerceProviderReceiptUnavailable(RuntimeError):
    pass


def init_schema(*, assume_yes: bool = False, dry_run: bool = False) -> dict[str, object]:
    if not assume_yes:
        raise RuntimeError("Explicit human approval required: pass --yes")
    if dry_run:
        return {
            "migration": MIGRATION_VERSION,
            "checksum": MIGRATION_CHECKSUM,
            "dry_run": True,
            "schema_ready": False,
            "human_authority_final": True,
        }
    try:
        with postgres_db.connect() as connection:
            for statement in SCHEMA_STATEMENTS:
                connection.execute(statement)
            connection.commit()
    except Exception as exc:
        raise CommerceProviderReceiptUnavailable("commerce_provider_receipt_schema_init_failed") from exc
    return {
        "migration": MIGRATION_VERSION,
        "checksum": MIGRATION_CHECKSUM,
        "dry_run": False,
        "schema_ready": True,
        "human_authority_final": True,
    }


def record(
    *,
    owner_identity_id: object,
    kind: object,
    subject_id: object,
    provider_receipt: object,
) -> dict[str, object]:
    if not isinstance(provider_receipt, Mapping):
        raise ValueError("provider_receipt_invalid")
    owner = str(uuid.UUID(str(owner_identity_id)))
    kind_value = str(kind or "").strip()
    if kind_value not in {"payment","payment_webhook","payment_refund","pod","pod_webhook"}:
        raise ValueError("provider_receipt_kind_invalid")
    subject = str(subject_id or "").strip()
    provider_id = str(provider_receipt.get("provider_id") or "").strip()
    provider_reference = str(provider_receipt.get("provider_reference") or "").strip()
    provider_state = str(provider_receipt.get("provider_state") or "").strip().upper()
    idempotency_key = str(provider_receipt.get("idempotency_key") or "").strip()
    receipt_hash = str(provider_receipt.get("receipt_hash") or "").strip()
    if not all((subject, provider_id, provider_reference, provider_state, idempotency_key, receipt_hash)):
        raise ValueError("provider_receipt_fields_missing")
    try:
        with postgres_db.connect() as connection:
            row = connection.execute(
                """INSERT INTO oap_commerce_provider_receipts(
                       receipt_id,owner_identity_id,kind,subject_id,provider_id,
                       provider_reference,provider_state,idempotency_key,receipt_hash
                   ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                   ON CONFLICT(kind,provider_id,idempotency_key) DO UPDATE
                   SET provider_reference=EXCLUDED.provider_reference,
                       provider_state=EXCLUDED.provider_state,
                       receipt_hash=EXCLUDED.receipt_hash
                   RETURNING receipt_id,kind,subject_id,provider_reference,
                             provider_state,receipt_hash,created_at""",
                (
                    str(uuid.uuid4()), owner, kind_value, subject, provider_id,
                    provider_reference, provider_state, idempotency_key, receipt_hash,
                ),
            ).fetchone()
            connection.commit()
    except Exception as exc:
        raise CommerceProviderReceiptUnavailable("commerce_provider_receipt_record_failed") from exc
    values = tuple(row)
    return {
        "receipt_id": str(values[0]),
        "kind": str(values[1]),
        "subject_id": str(values[2]),
        "provider_reference": str(values[3]),
        "provider_state": str(values[4]),
        "receipt_hash": str(values[5]),
        "created_at": values[6].isoformat(),
        "secret_values_exposed": False,
    }


def owner_for_subject(subject_id: object) -> str | None:
    subject = str(subject_id or "").strip()
    if not subject:
        raise ValueError("provider_receipt_subject_required")
    try:
        with postgres_db.connect(readonly=True) as connection:
            row = connection.execute(
                """SELECT owner_identity_id FROM oap_commerce_provider_receipts
                   WHERE subject_id=%s ORDER BY created_at ASC LIMIT 1""",
                (subject,),
            ).fetchone()
    except Exception as exc:
        raise CommerceProviderReceiptUnavailable(
            "commerce_provider_receipt_owner_read_failed"
        ) from exc
    return None if row is None else str(row[0])


def status() -> dict[str, object]:
    return {
        "system": "OAP Commerce Provider Receipts",
        "backend": "postgresql",
        "payment_receipts": True,
        "pod_receipts": True,
        "webhook_receipts": True,
        "secret_values_persisted": False,
        "human_authority_final": True,
    }
