"""Durable evidence store for OAP real-bank authorisation readiness.

Append-only by design: evidence is never updated or deleted in place. The
latest event for each PRA/FCA evidence category is projected into the current
readiness register. This store does not grant regulatory authorisation.
"""
from __future__ import annotations

import hashlib
import uuid
from typing import Any

from . import bank_authorisation, postgres_db

BANK_EVIDENCE_MIGRATION_VERSION = "bank_authorisation_evidence_v1"
BANK_EVIDENCE_SCHEMA_STATEMENTS = (
    """CREATE TABLE IF NOT EXISTS oap_bank_authorisation_evidence (
        evidence_id UUID PRIMARY KEY,
        category TEXT NOT NULL,
        status TEXT NOT NULL CHECK (status IN ('DRAFT','REVIEWED','ACCEPTED','REJECTED')),
        evidence_reference TEXT NOT NULL,
        reviewed_by TEXT NOT NULL DEFAULT '',
        notes TEXT NOT NULL DEFAULT '',
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE INDEX IF NOT EXISTS ix_bank_authorisation_evidence_category_created
       ON oap_bank_authorisation_evidence(category, created_at DESC)""",
)
BANK_EVIDENCE_MIGRATION_CHECKSUM = hashlib.sha256(
    "\n".join(BANK_EVIDENCE_SCHEMA_STATEMENTS).encode()
).hexdigest()
_ALLOWED_STATUS = {"DRAFT", "REVIEWED", "ACCEPTED", "REJECTED"}


class BankEvidenceUnavailable(RuntimeError):
    """Raised when durable bank evidence cannot be safely read or written."""


def _clean(value: object, *, limit: int) -> str:
    return str(value or "").strip()[:limit]


def init_schema(*, assume_yes: bool = False, dry_run: bool = False) -> dict[str, Any]:
    """Create the append-only evidence schema after explicit Human Authority approval."""

    if not assume_yes:
        raise RuntimeError("Explicit human approval required: pass --yes")
    if dry_run:
        return {
            "migration": BANK_EVIDENCE_MIGRATION_VERSION,
            "checksum": BANK_EVIDENCE_MIGRATION_CHECKSUM,
            "dry_run": True,
            "schema_ready": False,
            "human_authority_final": True,
        }
    try:
        with postgres_db.connect() as connection:
            for statement in BANK_EVIDENCE_SCHEMA_STATEMENTS:
                connection.execute(statement)
            connection.commit()
    except Exception as exc:
        raise BankEvidenceUnavailable("bank_evidence_schema_init_failed") from exc
    status = schema_status()
    if not status["schema_ready"]:
        raise BankEvidenceUnavailable("bank_evidence_schema_verification_failed")
    return {
        **status,
        "migration": BANK_EVIDENCE_MIGRATION_VERSION,
        "checksum": BANK_EVIDENCE_MIGRATION_CHECKSUM,
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
                     AND table_name='oap_bank_authorisation_evidence'
                   LIMIT 1"""
            ).fetchone()
            result["evidence_table_ready"] = row is not None
            result["schema_ready"] = row is not None
    except Exception:  # noqa: BLE001
        result["error"] = "bank_evidence_store_unavailable"
    return result


def record_evidence(
    *,
    category: object,
    status: object,
    evidence_reference: object,
    reviewed_by: object = "",
    notes: object = "",
) -> dict[str, object]:
    """Append one governed evidence event.

    ACCEPTED means accepted into OAP's internal application evidence pack. It
    does not mean PRA/FCA approval or bank authorisation.
    """

    category_value = _clean(category, limit=120)
    status_value = _clean(status, limit=20).upper()
    reference = _clean(evidence_reference, limit=1000)
    reviewer = _clean(reviewed_by, limit=240)
    notes_value = _clean(notes, limit=2000)

    if category_value not in bank_authorisation.PRA_FCA_EVIDENCE:
        raise ValueError("unknown_bank_evidence_category")
    if status_value not in _ALLOWED_STATUS:
        raise ValueError("invalid_bank_evidence_status")
    if not reference:
        raise ValueError("bank_evidence_reference_required")
    if status_value in {"REVIEWED", "ACCEPTED", "REJECTED"} and not reviewer:
        raise ValueError("bank_evidence_reviewer_required")

    evidence_id = str(uuid.uuid4())
    try:
        with postgres_db.connect() as connection:
            row = connection.execute(
                """INSERT INTO oap_bank_authorisation_evidence(
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
        raise BankEvidenceUnavailable("bank_evidence_write_failed") from exc

    return {
        "evidence_id": evidence_id,
        "category": category_value,
        "status": status_value,
        "evidence_reference": reference,
        "reviewed_by": reviewer,
        "created_at": row[0].isoformat(),
        "regulator_authorisation_granted": False,
        "regulated_execution_enabled": False,
        "human_authority_final": True,
    }


def latest_register() -> dict[str, dict[str, object]]:
    """Project latest append-only event per category into readiness input."""

    register = bank_authorisation.evidence_register()
    try:
        with postgres_db.connect(readonly=True) as connection:
            exists = connection.execute(
                """SELECT 1 FROM information_schema.tables
                   WHERE table_schema='public'
                     AND table_name='oap_bank_authorisation_evidence'
                   LIMIT 1"""
            ).fetchone()
            if exists is None:
                return register
            rows = connection.execute(
                """SELECT DISTINCT ON (category)
                       category,status,evidence_reference,reviewed_by,created_at
                   FROM oap_bank_authorisation_evidence
                   ORDER BY category,created_at DESC,evidence_id DESC"""
            ).fetchall()
    except Exception as exc:
        raise BankEvidenceUnavailable("bank_evidence_read_failed") from exc

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


def readiness_status() -> dict[str, Any]:
    """Return bank readiness from durable accepted evidence."""

    return bank_authorisation.readiness_status(evidence=latest_register())
