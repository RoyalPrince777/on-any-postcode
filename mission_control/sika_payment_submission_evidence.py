"""Durable provider-submission evidence for SIKA payments.

Records submission receipts and uncertain outcomes without retrying providers.
This module does not call providers, change payment state automatically, post
journals, settle funds, or move money.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass

from . import postgres_db

MIGRATION_VERSION = "sika_payment_submission_evidence_v1"
SCHEMA_STATEMENTS = (
    """CREATE TABLE IF NOT EXISTS oap_sika_payment_submission_evidence (
        evidence_id TEXT PRIMARY KEY,
        payment_id TEXT NOT NULL,
        idempotency_key TEXT NOT NULL,
        provider_id TEXT NOT NULL,
        provider_reference TEXT,
        outcome TEXT NOT NULL CHECK (
            outcome IN ('ACCEPTED','REJECTED','UNCERTAIN')
        ),
        evidence_hash TEXT NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(provider_id,idempotency_key)
    )""",
    """CREATE INDEX IF NOT EXISTS ix_sika_submission_payment
       ON oap_sika_payment_submission_evidence(payment_id)""",
)
MIGRATION_CHECKSUM = hashlib.sha256(
    "\n".join(SCHEMA_STATEMENTS).encode()
).hexdigest()


class SubmissionEvidenceError(ValueError):
    """Raised when submission evidence is malformed or unsafe."""


class SubmissionEvidenceUnavailable(RuntimeError):
    """Raised when durable submission evidence cannot be accessed."""


def _required(value: object, *, error: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise SubmissionEvidenceError(error)
    return text


@dataclass(frozen=True)
class SubmissionEvidence:
    evidence_id: str
    payment_id: str
    idempotency_key: str
    provider_id: str
    provider_reference: str | None
    outcome: str
    evidence_hash: str

    @property
    def automatic_retry_allowed(self) -> bool:
        return False

    @property
    def human_review_required(self) -> bool:
        return self.outcome == "UNCERTAIN"


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
        raise SubmissionEvidenceUnavailable(
            "submission_evidence_schema_init_failed"
        ) from exc
    return {
        "migration": MIGRATION_VERSION,
        "checksum": MIGRATION_CHECKSUM,
        "dry_run": False,
        "schema_ready": True,
        "human_authority_final": True,
    }


def record(
    *,
    evidence_id: object,
    payment_id: object,
    idempotency_key: object,
    provider_id: object,
    provider_reference: object | None,
    outcome: object,
    evidence_hash: object,
) -> SubmissionEvidence:
    outcome_value = _required(outcome, error="submission_outcome_required").upper()
    if outcome_value not in {"ACCEPTED", "REJECTED", "UNCERTAIN"}:
        raise SubmissionEvidenceError("submission_outcome_invalid")

    provider_ref_value = None
    if provider_reference is not None:
        provider_ref_value = _required(
            provider_reference,
            error="provider_reference_invalid",
        )
    if outcome_value == "ACCEPTED" and provider_ref_value is None:
        raise SubmissionEvidenceError(
            "provider_reference_required_for_accepted_submission"
        )

    item = SubmissionEvidence(
        evidence_id=_required(evidence_id, error="evidence_id_required"),
        payment_id=_required(payment_id, error="payment_id_required"),
        idempotency_key=_required(
            idempotency_key,
            error="idempotency_key_required",
        ),
        provider_id=_required(provider_id, error="provider_id_required"),
        provider_reference=provider_ref_value,
        outcome=outcome_value,
        evidence_hash=_required(evidence_hash, error="evidence_hash_required"),
    )
    try:
        with postgres_db.connect() as connection:
            connection.execute(
                """INSERT INTO oap_sika_payment_submission_evidence(
                       evidence_id,payment_id,idempotency_key,provider_id,
                       provider_reference,outcome,evidence_hash
                   ) VALUES (%s,%s,%s,%s,%s,%s,%s)""",
                (
                    item.evidence_id,
                    item.payment_id,
                    item.idempotency_key,
                    item.provider_id,
                    item.provider_reference,
                    item.outcome,
                    item.evidence_hash,
                ),
            )
            connection.commit()
    except Exception as exc:
        raise SubmissionEvidenceUnavailable(
            "submission_evidence_record_failed"
        ) from exc
    return item


def status() -> dict[str, object]:
    return {
        "system": "SIKA Payment Submission Evidence",
        "first_party": True,
        "backend": "postgresql",
        "durable_submission_receipts": True,
        "provider_idempotency_replay_protection": True,
        "uncertain_outcome_state": True,
        "automatic_retry": False,
        "provider_calling": False,
        "payment_state_mutation": False,
        "journal_posting": False,
        "settlement_execution": False,
        "money_movement": False,
        "human_authority_final": True,
    }
