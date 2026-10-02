"""Durable reconciliation exception ownership for SIKA.

Persists mismatch/exception cases derived from runtime reconciliation. It does
not alter journals, retry providers, settle funds, or move money.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass

from . import postgres_db

MIGRATION_VERSION = "sika_reconciliation_exception_store_v1"
SCHEMA_STATEMENTS = (
    """CREATE TABLE IF NOT EXISTS oap_sika_reconciliation_exceptions (
        exception_id TEXT PRIMARY KEY,
        payment_id TEXT NOT NULL,
        provider_id TEXT NOT NULL,
        provider_reference TEXT NOT NULL,
        reconciliation_state TEXT NOT NULL CHECK (
            reconciliation_state IN ('PENDING','MISMATCH','EXCEPTION')
        ),
        owner_reference TEXT,
        resolution_status TEXT NOT NULL CHECK (
            resolution_status IN ('OPEN','IN_REVIEW','RESOLVED','CLOSED')
        ),
        resolution_note TEXT,
        evidence_hash TEXT NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE INDEX IF NOT EXISTS ix_sika_recon_exception_payment
       ON oap_sika_reconciliation_exceptions(payment_id)""",
    """CREATE INDEX IF NOT EXISTS ix_sika_recon_exception_status
       ON oap_sika_reconciliation_exceptions(resolution_status)""",
)
MIGRATION_CHECKSUM = hashlib.sha256(
    "\n".join(SCHEMA_STATEMENTS).encode()
).hexdigest()


class ReconciliationExceptionError(ValueError):
    """Raised when exception ownership or resolution rules are violated."""


class ReconciliationExceptionUnavailable(RuntimeError):
    """Raised when durable exception state cannot be accessed."""


@dataclass(frozen=True)
class ReconciliationException:
    exception_id: str
    payment_id: str
    provider_id: str
    provider_reference: str
    reconciliation_state: str
    owner_reference: str | None
    resolution_status: str
    resolution_note: str | None
    evidence_hash: str

    @property
    def human_review_required(self) -> bool:
        return self.resolution_status in {"OPEN", "IN_REVIEW"}


def _required(value: object, *, error: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ReconciliationExceptionError(error)
    return text


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
        raise ReconciliationExceptionUnavailable(
            "reconciliation_exception_schema_init_failed"
        ) from exc
    return {
        "migration": MIGRATION_VERSION,
        "checksum": MIGRATION_CHECKSUM,
        "dry_run": False,
        "schema_ready": True,
        "human_authority_final": True,
    }


def create_case(
    *,
    exception_id: object,
    payment_id: object,
    provider_id: object,
    provider_reference: object,
    reconciliation_state: object,
    evidence_hash: object,
) -> ReconciliationException:
    state = _required(
        reconciliation_state,
        error="reconciliation_state_required",
    ).upper()
    if state not in {"PENDING", "MISMATCH", "EXCEPTION"}:
        raise ReconciliationExceptionError("reconciliation_state_invalid")

    case = ReconciliationException(
        exception_id=_required(exception_id, error="exception_id_required"),
        payment_id=_required(payment_id, error="payment_id_required"),
        provider_id=_required(provider_id, error="provider_id_required"),
        provider_reference=_required(
            provider_reference,
            error="provider_reference_required",
        ),
        reconciliation_state=state,
        owner_reference=None,
        resolution_status="OPEN",
        resolution_note=None,
        evidence_hash=_required(evidence_hash, error="evidence_hash_required"),
    )
    try:
        with postgres_db.connect() as connection:
            connection.execute(
                """INSERT INTO oap_sika_reconciliation_exceptions(
                       exception_id,payment_id,provider_id,provider_reference,
                       reconciliation_state,owner_reference,resolution_status,
                       resolution_note,evidence_hash
                   ) VALUES (%s,%s,%s,%s,%s,NULL,'OPEN',NULL,%s)""",
                (
                    case.exception_id,
                    case.payment_id,
                    case.provider_id,
                    case.provider_reference,
                    case.reconciliation_state,
                    case.evidence_hash,
                ),
            )
            connection.commit()
    except Exception as exc:
        raise ReconciliationExceptionUnavailable(
            "reconciliation_exception_create_failed"
        ) from exc
    return case


def status() -> dict[str, object]:
    return {
        "system": "SIKA Reconciliation Exception Store",
        "first_party": True,
        "backend": "postgresql",
        "persistent_exception_cases": True,
        "owner_assignment_supported": True,
        "resolution_lifecycle": ["OPEN", "IN_REVIEW", "RESOLVED", "CLOSED"],
        "automatic_retry": False,
        "journal_mutation": False,
        "provider_calling": False,
        "settlement_execution": False,
        "money_movement": False,
        "human_authority_final": True,
    }
