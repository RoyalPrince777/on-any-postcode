"""Persistent SIKA payment dispute cases and append-only chronology.

Captures dispute evidence and case chronology. It does not decide liability,
file external chargebacks, mutate journals, or move money.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass

from . import postgres_db

MIGRATION_VERSION = "sika_payment_disputes_v1"
SCHEMA_STATEMENTS = (
    """CREATE TABLE IF NOT EXISTS oap_sika_payment_disputes (
        dispute_id TEXT PRIMARY KEY,
        payment_id TEXT NOT NULL,
        reason_code TEXT NOT NULL,
        status TEXT NOT NULL CHECK (
            status IN ('OPEN','EVIDENCE','REVIEW','RESOLVED','CLOSED')
        ),
        owner_reference TEXT,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE TABLE IF NOT EXISTS oap_sika_payment_dispute_events (
        event_id TEXT PRIMARY KEY,
        dispute_id TEXT NOT NULL,
        event_type TEXT NOT NULL,
        evidence_hash TEXT NOT NULL,
        note TEXT,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE OR REPLACE FUNCTION oap_reject_dispute_event_mutation()
       RETURNS trigger AS $$
       BEGIN
         RAISE EXCEPTION 'dispute_event_append_only';
       END;
       $$ LANGUAGE plpgsql""",
    """DROP TRIGGER IF EXISTS oap_dispute_events_immutable
       ON oap_sika_payment_dispute_events""",
    """CREATE TRIGGER oap_dispute_events_immutable
       BEFORE UPDATE OR DELETE ON oap_sika_payment_dispute_events
       FOR EACH ROW EXECUTE FUNCTION oap_reject_dispute_event_mutation()""",
)
MIGRATION_CHECKSUM = hashlib.sha256(
    "\n".join(SCHEMA_STATEMENTS).encode()
).hexdigest()


class DisputeError(ValueError):
    """Raised when dispute evidence is invalid."""


class DisputeUnavailable(RuntimeError):
    """Raised when durable dispute state cannot be accessed."""


def _required(value: object, *, error: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise DisputeError(error)
    return text


@dataclass(frozen=True)
class DisputeCase:
    dispute_id: str
    payment_id: str
    reason_code: str
    status: str
    owner_reference: str | None = None


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
        raise DisputeUnavailable("dispute_schema_init_failed") from exc
    return {
        "migration": MIGRATION_VERSION,
        "checksum": MIGRATION_CHECKSUM,
        "dry_run": False,
        "schema_ready": True,
        "human_authority_final": True,
    }


def open_case(
    *,
    dispute_id: object,
    payment_id: object,
    reason_code: object,
) -> DisputeCase:
    case = DisputeCase(
        dispute_id=_required(dispute_id, error="dispute_id_required"),
        payment_id=_required(payment_id, error="payment_id_required"),
        reason_code=_required(reason_code, error="reason_code_required"),
        status="OPEN",
    )
    try:
        with postgres_db.connect() as connection:
            connection.execute(
                """INSERT INTO oap_sika_payment_disputes(
                       dispute_id,payment_id,reason_code,status,owner_reference
                   ) VALUES (%s,%s,%s,'OPEN',NULL)""",
                (case.dispute_id, case.payment_id, case.reason_code),
            )
            connection.commit()
    except Exception as exc:
        raise DisputeUnavailable("dispute_create_failed") from exc
    return case


def append_event(
    *,
    event_id: object,
    dispute_id: object,
    event_type: object,
    evidence_hash: object,
    note: object | None = None,
) -> dict[str, object]:
    event = {
        "event_id": _required(event_id, error="event_id_required"),
        "dispute_id": _required(dispute_id, error="dispute_id_required"),
        "event_type": _required(event_type, error="event_type_required"),
        "evidence_hash": _required(evidence_hash, error="evidence_hash_required"),
        "note": None if note is None else str(note).strip() or None,
    }
    try:
        with postgres_db.connect() as connection:
            connection.execute(
                """INSERT INTO oap_sika_payment_dispute_events(
                       event_id,dispute_id,event_type,evidence_hash,note
                   ) VALUES (%s,%s,%s,%s,%s)""",
                (
                    event["event_id"],
                    event["dispute_id"],
                    event["event_type"],
                    event["evidence_hash"],
                    event["note"],
                ),
            )
            connection.commit()
    except Exception as exc:
        raise DisputeUnavailable("dispute_event_append_failed") from exc
    return event


def status() -> dict[str, object]:
    return {
        "system": "SIKA Payment Disputes",
        "first_party": True,
        "persistent_dispute_cases": True,
        "append_only_chronology": True,
        "evidence_hash_required": True,
        "external_chargeback_filing": False,
        "liability_decision": False,
        "journal_mutation": False,
        "money_movement": False,
        "human_authority_final": True,
    }
