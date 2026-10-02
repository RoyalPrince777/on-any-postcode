"""Durable production-evidence store for SIKA regulated execution readiness.

Append-only by design. This store records software/operational production proof.
It does not grant regulator authorisation and does not execute or settle money.
"""
from __future__ import annotations

import hashlib
import uuid
from typing import Any

from . import postgres_db

PRODUCTION_EVIDENCE = (
    "provider_production_environment",
    "provider_authority_scope",
    "settlement_receipt_contract",
    "refund_reversal_contract",
    "webhook_signature_verification",
    "idempotency_controls",
    "ledger_reconciliation",
    "provider_runtime_readback",
)

MIGRATION_VERSION = "sika_production_evidence_v1"
SCHEMA_STATEMENTS = (
    """CREATE TABLE IF NOT EXISTS oap_sika_production_evidence (
        evidence_id UUID PRIMARY KEY,
        category TEXT NOT NULL,
        status TEXT NOT NULL CHECK (status IN ('DRAFT','REVIEWED','ACCEPTED','REJECTED')),
        evidence_reference TEXT NOT NULL,
        reviewed_by TEXT NOT NULL DEFAULT '',
        notes TEXT NOT NULL DEFAULT '',
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE INDEX IF NOT EXISTS ix_sika_production_evidence_category_created
       ON oap_sika_production_evidence(category, created_at DESC)""",
)
MIGRATION_CHECKSUM = hashlib.sha256(
    "\n".join(SCHEMA_STATEMENTS).encode()
).hexdigest()
_ALLOWED_STATUS = {"DRAFT", "REVIEWED", "ACCEPTED", "REJECTED"}


class ProductionEvidenceUnavailable(RuntimeError):
    """Raised when durable production evidence cannot be read or written."""


def _clean(value: object, *, limit: int) -> str:
    return str(value or "").strip()[:limit]


def init_schema(*, assume_yes: bool = False, dry_run: bool = False) -> dict[str, Any]:
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
        raise ProductionEvidenceUnavailable(
            "sika_production_evidence_schema_init_failed"
        ) from exc
    status = schema_status()
    if not status["schema_ready"]:
        raise ProductionEvidenceUnavailable(
            "sika_production_evidence_schema_verification_failed"
        )
    return {
        **status,
        "migration": MIGRATION_VERSION,
        "checksum": MIGRATION_CHECKSUM,
        "dry_run": False,
        "human_authority_final": True,
    }


def schema_status() -> dict[str, object]:
    result: dict[str, object] = {
        "database_reachable": False,
        "evidence_table_ready": False,
        "schema_ready": False,
        "error": None,
    }
    try:
        with postgres_db.connect(readonly=True) as connection:
            result["database_reachable"] = True
            row = connection.execute(
                """SELECT 1 FROM information_schema.tables
                   WHERE table_schema='public'
                     AND table_name='oap_sika_production_evidence'
                   LIMIT 1"""
            ).fetchone()
            result["evidence_table_ready"] = row is not None
            result["schema_ready"] = row is not None
    except Exception:  # noqa: BLE001
        result["error"] = "sika_production_evidence_store_unavailable"
    return result


def record_evidence(
    *,
    category: object,
    status: object,
    evidence_reference: object,
    reviewed_by: object = "",
    notes: object = "",
) -> dict[str, object]:
    category_value = _clean(category, limit=120)
    status_value = _clean(status, limit=20).upper()
    reference = _clean(evidence_reference, limit=1000)
    reviewer = _clean(reviewed_by, limit=240)
    notes_value = _clean(notes, limit=2000)

    if category_value not in PRODUCTION_EVIDENCE:
        raise ValueError("unknown_sika_production_evidence_category")
    if status_value not in _ALLOWED_STATUS:
        raise ValueError("invalid_sika_production_evidence_status")
    if not reference:
        raise ValueError("sika_production_evidence_reference_required")
    if status_value in {"REVIEWED", "ACCEPTED", "REJECTED"} and not reviewer:
        raise ValueError("sika_production_evidence_reviewer_required")

    evidence_id = str(uuid.uuid4())
    try:
        with postgres_db.connect() as connection:
            row = connection.execute(
                """INSERT INTO oap_sika_production_evidence(
                       evidence_id,category,status,evidence_reference,reviewed_by,notes
                   ) VALUES (%s,%s,%s,%s,%s,%s)
                   RETURNING created_at""",
                (
                    evidence_id,
                    category_value,
                    status_value,
                    reference,
                    reviewer,
                    notes_value,
                ),
            ).fetchone()
            connection.commit()
    except Exception as exc:
        raise ProductionEvidenceUnavailable(
            "sika_production_evidence_write_failed"
        ) from exc

    return {
        "evidence_id": evidence_id,
        "category": category_value,
        "status": status_value,
        "evidence_reference": reference,
        "reviewed_by": reviewer,
        "created_at": row[0].isoformat(),
        "production_gate_passed": False,
        "money_moved": False,
        "human_authority_final": True,
    }


def latest_register() -> dict[str, dict[str, object]]:
    register = {
        key: {
            "proven": False,
            "status": "MISSING",
            "evidence_reference": None,
            "reviewed_by": None,
        }
        for key in PRODUCTION_EVIDENCE
    }
    try:
        with postgres_db.connect(readonly=True) as connection:
            exists = connection.execute(
                """SELECT 1 FROM information_schema.tables
                   WHERE table_schema='public'
                     AND table_name='oap_sika_production_evidence'
                   LIMIT 1"""
            ).fetchone()
            if exists is None:
                return register
            rows = connection.execute(
                """SELECT DISTINCT ON (category)
                       category,status,evidence_reference,reviewed_by,created_at
                   FROM oap_sika_production_evidence
                   ORDER BY category,created_at DESC,evidence_id DESC"""
            ).fetchall()
    except Exception as exc:
        raise ProductionEvidenceUnavailable(
            "sika_production_evidence_read_failed"
        ) from exc

    for row in rows:
        category = str(row[0])
        if category not in register:
            continue
        register[category] = {
            "proven": str(row[1]) == "ACCEPTED",
            "status": str(row[1]),
            "evidence_reference": str(row[2]),
            "reviewed_by": str(row[3]),
            "recorded_at": row[4].isoformat(),
        }
    return register


def readiness_status() -> dict[str, object]:
    register = latest_register()
    proven = [key for key in PRODUCTION_EVIDENCE if register[key]["proven"]]
    missing = [key for key in PRODUCTION_EVIDENCE if key not in proven]
    return {
        "evidence_total": len(PRODUCTION_EVIDENCE),
        "evidence_proven": len(proven),
        "evidence_missing": tuple(missing),
        "production_gate_passed": not missing,
        "money_movement_enabled": False,
        "human_authority_final": True,
    }
