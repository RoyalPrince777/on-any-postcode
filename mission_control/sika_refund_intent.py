"""Persistent SIKA refund intent and compensating journal evidence.

Refunds must link to an original settled payment. The module can build a
compensating double-entry reversal but does not post it, call providers,
settle funds, or move money.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from . import postgres_db, sika_double_entry, sika_payment_orchestrator

MIGRATION_VERSION = "sika_refund_intent_v1"
SCHEMA_STATEMENTS = (
    """CREATE TABLE IF NOT EXISTS oap_sika_refund_intents (
        refund_id TEXT PRIMARY KEY,
        original_payment_id TEXT NOT NULL,
        idempotency_key TEXT NOT NULL UNIQUE,
        amount NUMERIC(24,2) NOT NULL CHECK (amount > 0),
        currency TEXT NOT NULL,
        status TEXT NOT NULL CHECK (
            status IN ('DRAFT','REVIEW','AUTHORISED','SUBMITTED','SETTLED','FAILED','CANCELLED')
        ),
        reason TEXT NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE INDEX IF NOT EXISTS ix_sika_refunds_original_payment
       ON oap_sika_refund_intents(original_payment_id)""",
)
MIGRATION_CHECKSUM = hashlib.sha256(
    "\n".join(SCHEMA_STATEMENTS).encode()
).hexdigest()


class RefundError(ValueError):
    """Raised when refund rules are violated."""


class RefundUnavailable(RuntimeError):
    """Raised when durable refund state cannot be accessed."""


def _required(value: object, *, error: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise RefundError(error)
    return text


def _amount(value: object) -> Decimal:
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise RefundError("refund_amount_invalid") from exc
    if not parsed.is_finite() or parsed <= 0:
        raise RefundError("refund_amount_invalid")
    return parsed.quantize(Decimal("0.01"))


@dataclass(frozen=True)
class RefundIntent:
    refund_id: str
    original_payment_id: str
    idempotency_key: str
    amount: Decimal
    currency: str
    status: str
    reason: str


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
        raise RefundUnavailable("refund_schema_init_failed") from exc
    return {
        "migration": MIGRATION_VERSION,
        "checksum": MIGRATION_CHECKSUM,
        "dry_run": False,
        "schema_ready": True,
        "human_authority_final": True,
    }


def prepare(
    *,
    refund_id: object,
    idempotency_key: object,
    original_payment: sika_payment_orchestrator.PaymentIntent,
    amount: object,
    reason: object,
) -> RefundIntent:
    if original_payment.status != "SETTLED":
        raise RefundError("original_payment_not_settled")
    amount_value = _amount(amount)
    if amount_value > original_payment.amount:
        raise RefundError("refund_exceeds_original_payment")

    intent = RefundIntent(
        refund_id=_required(refund_id, error="refund_id_required"),
        original_payment_id=original_payment.payment_id,
        idempotency_key=_required(idempotency_key, error="idempotency_key_required"),
        amount=amount_value,
        currency=original_payment.currency,
        status="DRAFT",
        reason=_required(reason, error="refund_reason_required"),
    )
    try:
        with postgres_db.connect() as connection:
            connection.execute(
                """INSERT INTO oap_sika_refund_intents(
                       refund_id,original_payment_id,idempotency_key,amount,
                       currency,status,reason
                   ) VALUES (%s,%s,%s,%s,%s,'DRAFT',%s)""",
                (
                    intent.refund_id,
                    intent.original_payment_id,
                    intent.idempotency_key,
                    intent.amount,
                    intent.currency,
                    intent.reason,
                ),
            )
            connection.commit()
    except Exception as exc:
        raise RefundUnavailable("refund_intent_create_failed") from exc
    return intent


def compensating_journal(
    *,
    refund: RefundIntent,
    original_journal: sika_double_entry.JournalBatch,
    journal_id: object,
) -> sika_double_entry.JournalBatch:
    original_debits = sum(
        (
            line.amount
            for line in original_journal.lines
            if line.currency == refund.currency
            and line.side is sika_double_entry.Side.DEBIT
        ),
        Decimal("0.00"),
    )
    if refund.amount != original_debits:
        raise RefundError("partial_refund_requires_allocation_model")
    return sika_double_entry.reversal_batch(
        original=original_journal,
        journal_id=journal_id,
        reference=f"refund:{refund.refund_id}:payment:{refund.original_payment_id}",
    )


def status() -> dict[str, object]:
    return {
        "system": "SIKA Refund Intent",
        "first_party": True,
        "persistent_refund_intent": True,
        "original_payment_linkage": True,
        "settled_payment_required": True,
        "refund_cap_enforced": True,
        "compensating_journal_supported": True,
        "partial_refund_auto_allocation": False,
        "journal_posting": False,
        "provider_calling": False,
        "settlement_execution": False,
        "money_movement": False,
        "human_authority_final": True,
    }
