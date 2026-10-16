"""Durable SIKA human-rights review receipts and remedy cases.

Persists the outcome of the deterministic SIKA Human Rights Gate and provides
an auditable appeal/remedy workflow. It does not create legal rights, override
law, reverse financial actions automatically, or move money.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass

from . import postgres_db, sika_human_rights_gate

MIGRATION_VERSION = "sika_human_rights_remedy_v1"
SCHEMA_STATEMENTS = (
    """CREATE TABLE IF NOT EXISTS oap_sika_human_rights_reviews (
        review_id TEXT PRIMARY KEY,
        action_type TEXT NOT NULL,
        subject_reference TEXT NOT NULL,
        evidence_reference TEXT NOT NULL,
        reason_code TEXT NOT NULL,
        review_state TEXT NOT NULL CHECK (
            review_state IN ('PASS_TO_HUMAN_REVIEW','HOLD')
        ),
        remedy_available BOOLEAN NOT NULL,
        explanation_available BOOLEAN NOT NULL,
        evidence_hash TEXT NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE TABLE IF NOT EXISTS oap_sika_human_rights_appeals (
        appeal_id TEXT PRIMARY KEY,
        review_id TEXT NOT NULL,
        subject_reference TEXT NOT NULL,
        status TEXT NOT NULL CHECK (
            status IN ('OPEN','IN_REVIEW','UPHELD','REMEDIED','CLOSED')
        ),
        owner_reference TEXT,
        appeal_reason TEXT NOT NULL,
        resolution_note TEXT,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE INDEX IF NOT EXISTS ix_sika_hr_appeals_review
       ON oap_sika_human_rights_appeals(review_id)""",
)
MIGRATION_CHECKSUM = hashlib.sha256(
    "\n".join(SCHEMA_STATEMENTS).encode()
).hexdigest()


class HumanRightsRemedyError(ValueError):
    """Raised when durable review/remedy rules are violated."""


class HumanRightsRemedyUnavailable(RuntimeError):
    """Raised when durable rights state cannot be accessed safely."""


def _required(value: object, *, error: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise HumanRightsRemedyError(error)
    return text


@dataclass(frozen=True)
class HumanRightsAppeal:
    appeal_id: str
    review_id: str
    subject_reference: str
    status: str
    owner_reference: str | None
    appeal_reason: str
    resolution_note: str | None = None

    @property
    def human_review_required(self) -> bool:
        return self.status in {"OPEN", "IN_REVIEW"}


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
        raise HumanRightsRemedyUnavailable("human_rights_remedy_schema_init_failed") from exc
    return {
        "migration": MIGRATION_VERSION,
        "checksum": MIGRATION_CHECKSUM,
        "dry_run": False,
        "schema_ready": True,
        "human_authority_final": True,
    }


def persist_review(
    *,
    review_id: object,
    review: sika_human_rights_gate.HumanRightsReview,
    evidence_hash: object,
) -> dict[str, object]:
    row = {
        "review_id": _required(review_id, error="review_id_required"),
        "action_type": review.action_type,
        "subject_reference": review.subject_reference,
        "evidence_reference": review.evidence_reference,
        "reason_code": review.reason_code,
        "review_state": review.state,
        "remedy_available": review.remedy_available,
        "explanation_available": review.explanation_available,
        "evidence_hash": _required(evidence_hash, error="evidence_hash_required"),
    }
    try:
        with postgres_db.connect() as connection:
            connection.execute(
                """INSERT INTO oap_sika_human_rights_reviews(
                       review_id,action_type,subject_reference,evidence_reference,
                       reason_code,review_state,remedy_available,
                       explanation_available,evidence_hash
                   ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                tuple(row.values()),
            )
            connection.commit()
    except Exception as exc:
        raise HumanRightsRemedyUnavailable("human_rights_review_persist_failed") from exc
    return row


def open_appeal(
    *,
    appeal_id: object,
    review_id: object,
    subject_reference: object,
    appeal_reason: object,
) -> HumanRightsAppeal:
    appeal = HumanRightsAppeal(
        appeal_id=_required(appeal_id, error="appeal_id_required"),
        review_id=_required(review_id, error="review_id_required"),
        subject_reference=_required(subject_reference, error="subject_reference_required"),
        status="OPEN",
        owner_reference=None,
        appeal_reason=_required(appeal_reason, error="appeal_reason_required"),
    )
    try:
        with postgres_db.connect() as connection:
            connection.execute(
                """INSERT INTO oap_sika_human_rights_appeals(
                       appeal_id,review_id,subject_reference,status,
                       owner_reference,appeal_reason,resolution_note
                   ) VALUES (%s,%s,%s,'OPEN',NULL,%s,NULL)""",
                (
                    appeal.appeal_id,
                    appeal.review_id,
                    appeal.subject_reference,
                    appeal.appeal_reason,
                ),
            )
            connection.commit()
    except Exception as exc:
        raise HumanRightsRemedyUnavailable("human_rights_appeal_open_failed") from exc
    return appeal


def status() -> dict[str, object]:
    return {
        "system": "SIKA Human Rights Remedy Store",
        "first_party": True,
        "backend": "postgresql",
        "durable_review_receipts": True,
        "durable_appeals": True,
        "appeal_lifecycle": ["OPEN", "IN_REVIEW", "UPHELD", "REMEDIED", "CLOSED"],
        "owner_assignment_supported": True,
        "automatic_reversal": False,
        "creates_legal_entitlement": False,
        "overrides_applicable_law": False,
        "financial_execution": False,
        "money_movement": False,
        "human_authority_final": True,
    }
