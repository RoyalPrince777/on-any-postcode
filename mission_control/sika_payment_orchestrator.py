"""Persistent first-party SIKA Payment Intent + Orchestrator.

Owns durable payment intent identity and lifecycle state. It validates account
eligibility and keeps authorisation separate from provider submission. This
module does not call providers, post journals, settle funds, or move money.
"""
from __future__ import annotations

import hashlib
from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from . import postgres_db, sika_account_engine

MIGRATION_VERSION = "sika_payment_orchestrator_v1"
SCHEMA_STATEMENTS = (
    """CREATE TABLE IF NOT EXISTS oap_sika_payment_intents (
        payment_id TEXT PRIMARY KEY,
        idempotency_key TEXT NOT NULL UNIQUE,
        payer_account_id TEXT NOT NULL,
        payee_reference TEXT NOT NULL,
        amount NUMERIC(24,2) NOT NULL CHECK (amount > 0),
        currency TEXT NOT NULL,
        jurisdiction TEXT NOT NULL,
        status TEXT NOT NULL CHECK (
            status IN (
                'DRAFT','REVIEW','AUTHORISED','SUBMITTED',
                'SETTLED','FAILED','CANCELLED'
            )
        ),
        provider_reference TEXT,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE INDEX IF NOT EXISTS ix_sika_payment_intents_payer
       ON oap_sika_payment_intents(payer_account_id)""",
    """CREATE INDEX IF NOT EXISTS ix_sika_payment_intents_status
       ON oap_sika_payment_intents(status)""",
)
MIGRATION_CHECKSUM = hashlib.sha256(
    "\n".join(SCHEMA_STATEMENTS).encode()
).hexdigest()


class PaymentOrchestratorError(ValueError):
    """Raised when payment intent or state rules are violated."""


class PaymentOrchestratorUnavailable(RuntimeError):
    """Raised when durable payment state cannot be accessed safely."""


def _required(value: object, *, error: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise PaymentOrchestratorError(error)
    return text


def _amount(value: object) -> Decimal:
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise PaymentOrchestratorError("payment_amount_invalid") from exc
    if not parsed.is_finite() or parsed <= 0:
        raise PaymentOrchestratorError("payment_amount_invalid")
    return parsed.quantize(Decimal("0.01"))


@dataclass(frozen=True)
class PaymentIntent:
    payment_id: str
    idempotency_key: str
    payer_account_id: str
    payee_reference: str
    amount: Decimal
    currency: str
    jurisdiction: str
    status: str
    provider_reference: str | None = None

    @property
    def terminal(self) -> bool:
        return self.status in {"SETTLED", "FAILED", "CANCELLED"}

    @property
    def may_submit_to_provider(self) -> bool:
        return self.status == "AUTHORISED"

    def as_dict(self) -> dict[str, object]:
        return {
            "payment_id": self.payment_id,
            "idempotency_key": self.idempotency_key,
            "payer_account_id": self.payer_account_id,
            "payee_reference": self.payee_reference,
            "amount": f"{self.amount:.2f}",
            "currency": self.currency,
            "jurisdiction": self.jurisdiction,
            "status": self.status,
            "provider_reference": self.provider_reference,
            "terminal": self.terminal,
            "may_submit_to_provider": self.may_submit_to_provider,
        }


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
        raise PaymentOrchestratorUnavailable(
            "payment_orchestrator_schema_init_failed"
        ) from exc
    return {
        "migration": MIGRATION_VERSION,
        "checksum": MIGRATION_CHECKSUM,
        "dry_run": False,
        "schema_ready": True,
        "human_authority_final": True,
    }


def _row_to_intent(row: object) -> PaymentIntent:
    values = tuple(row)
    return PaymentIntent(
        payment_id=str(values[0]),
        idempotency_key=str(values[1]),
        payer_account_id=str(values[2]),
        payee_reference=str(values[3]),
        amount=Decimal(str(values[4])).quantize(Decimal("0.01")),
        currency=str(values[5]),
        jurisdiction=str(values[6]),
        status=str(values[7]),
        provider_reference=None if values[8] is None else str(values[8]),
    )


def create_intent(
    *,
    payment_id: object,
    idempotency_key: object,
    payer_account: sika_account_engine.BankAccount,
    payee_reference: object,
    amount: object,
    currency: object,
    jurisdiction: object,
) -> PaymentIntent:
    if not payer_account.customer_activity_allowed:
        raise PaymentOrchestratorError("payer_account_not_open")

    currency_value = _required(currency, error="payment_currency_required").upper()
    jurisdiction_value = _required(
        jurisdiction,
        error="payment_jurisdiction_required",
    )
    if payer_account.currency != currency_value:
        raise PaymentOrchestratorError("payer_currency_mismatch")
    if payer_account.jurisdiction != jurisdiction_value:
        raise PaymentOrchestratorError("payer_jurisdiction_mismatch")

    intent = PaymentIntent(
        payment_id=_required(payment_id, error="payment_id_required"),
        idempotency_key=_required(
            idempotency_key,
            error="idempotency_key_required",
        ),
        payer_account_id=payer_account.account_id,
        payee_reference=_required(
            payee_reference,
            error="payee_reference_required",
        ),
        amount=_amount(amount),
        currency=currency_value,
        jurisdiction=jurisdiction_value,
        status="DRAFT",
    )
    try:
        with postgres_db.connect() as connection:
            connection.execute(
                """INSERT INTO oap_sika_payment_intents(
                       payment_id,idempotency_key,payer_account_id,payee_reference,
                       amount,currency,jurisdiction,status
                   ) VALUES (%s,%s,%s,%s,%s,%s,%s,'DRAFT')""",
                (
                    intent.payment_id,
                    intent.idempotency_key,
                    intent.payer_account_id,
                    intent.payee_reference,
                    intent.amount,
                    intent.currency,
                    intent.jurisdiction,
                ),
            )
            connection.commit()
    except Exception as exc:
        raise PaymentOrchestratorUnavailable("payment_intent_create_failed") from exc
    return intent


def read_intent(payment_id: object) -> PaymentIntent | None:
    payment_id_value = _required(payment_id, error="payment_id_required")
    try:
        with postgres_db.connect(readonly=True) as connection:
            row = connection.execute(
                """SELECT payment_id,idempotency_key,payer_account_id,
                          payee_reference,amount,currency,jurisdiction,status,
                          provider_reference
                   FROM oap_sika_payment_intents
                   WHERE payment_id=%s""",
                (payment_id_value,),
            ).fetchone()
    except Exception as exc:
        raise PaymentOrchestratorUnavailable("payment_intent_read_failed") from exc
    return None if row is None else _row_to_intent(row)


def read_intent_by_provider_reference(provider_reference: object) -> PaymentIntent | None:
    provider_ref = _required(
        provider_reference,
        error="provider_reference_required",
    )
    try:
        with postgres_db.connect(readonly=True) as connection:
            row = connection.execute(
                """SELECT payment_id,idempotency_key,payer_account_id,
                          payee_reference,amount,currency,jurisdiction,status,
                          provider_reference
                   FROM oap_sika_payment_intents
                   WHERE provider_reference=%s
                   ORDER BY updated_at DESC
                   LIMIT 1""",
                (provider_ref,),
            ).fetchone()
    except Exception as exc:
        raise PaymentOrchestratorUnavailable(
            "payment_intent_provider_lookup_failed"
        ) from exc
    return None if row is None else _row_to_intent(row)


def _gateway_authorization_valid(
    value: object,
    *,
    intent: PaymentIntent,
) -> bool:
    if not isinstance(value, Mapping):
        return False
    required_hashes = (
        str(value.get("rights_record_hash") or ""),
        str(value.get("rights_gate_decision_hash") or ""),
    )
    if any(len(item) != 64 for item in required_hashes):
        return False
    return (
        value.get("transition_authorized") is True
        and value.get("target_status") == "AUTHORISED"
        and str(value.get("payment_id") or "") == intent.payment_id
        and str(value.get("payer_account_id") or "") == intent.payer_account_id
        and str(value.get("payee_reference") or "") == intent.payee_reference
        and str(value.get("amount") or "") == f"{intent.amount:.2f}"
        and str(value.get("currency") or "") == intent.currency
        and str(value.get("jurisdiction") or "") == intent.jurisdiction
        and value.get("human_authority_final") is True
        and value.get("provider_calling") is False
        and value.get("settlement_execution") is False
        and value.get("money_movement") is False
    )


def transition(
    *,
    payment_id: object,
    target_status: object,
    provider_reference: object | None = None,
    gateway_authorization: object | None = None,
) -> PaymentIntent:
    target = _required(target_status, error="payment_target_status_required").upper()
    allowed = {
        "DRAFT": {"REVIEW", "CANCELLED"},
        "REVIEW": {"AUTHORISED", "CANCELLED"},
        "AUTHORISED": {"SUBMITTED", "CANCELLED"},
        "SUBMITTED": {"SETTLED", "FAILED"},
        "SETTLED": set(),
        "FAILED": set(),
        "CANCELLED": set(),
    }
    if target not in allowed:
        raise PaymentOrchestratorError("payment_target_status_invalid")

    current = read_intent(payment_id)
    if current is None:
        raise PaymentOrchestratorError("payment_intent_not_found")
    if target == current.status:
        return current
    if target not in allowed[current.status]:
        raise PaymentOrchestratorError("payment_transition_not_allowed")
    if target == "AUTHORISED" and not _gateway_authorization_valid(
        gateway_authorization,
        intent=current,
    ):
        raise PaymentOrchestratorError("sika_pay_gateway_authorization_required")
    if target != "AUTHORISED" and gateway_authorization is not None:
        raise PaymentOrchestratorError(
            "gateway_authorization_only_allowed_for_authorised_transition"
        )

    provider_ref_value = current.provider_reference
    if target == "SUBMITTED":
        provider_ref_value = _required(
            provider_reference,
            error="provider_reference_required_for_submission",
        )
    elif provider_reference is not None:
        raise PaymentOrchestratorError(
            "provider_reference_only_allowed_on_submission"
        )

    try:
        with postgres_db.connect() as connection:
            row = connection.execute(
                """UPDATE oap_sika_payment_intents
                   SET status=%s,provider_reference=%s,
                       updated_at=CURRENT_TIMESTAMP
                   WHERE payment_id=%s AND status=%s
                   RETURNING payment_id,idempotency_key,payer_account_id,
                             payee_reference,amount,currency,jurisdiction,status,
                             provider_reference""",
                (
                    target,
                    provider_ref_value,
                    current.payment_id,
                    current.status,
                ),
            ).fetchone()
            if row is None:
                raise PaymentOrchestratorError("payment_state_changed")
            connection.commit()
    except PaymentOrchestratorError:
        raise
    except Exception as exc:
        raise PaymentOrchestratorUnavailable("payment_transition_failed") from exc

    return _row_to_intent(row)


def status() -> dict[str, object]:
    return {
        "system": "SIKA Payment Orchestrator",
        "first_party": True,
        "backend": "postgresql",
        "persistent_payment_intent": True,
        "idempotency_key_unique": True,
        "payer_account_binding": True,
        "payee_reference_binding": True,
        "currency_validation": True,
        "jurisdiction_validation": True,
        "sika_pay_gateway_required_for_authorisation": True,
        "direct_authorisation_bypass_allowed": False,
        "gateway_authorization_bound_to_payment": True,
        "gateway_authorization_requires_rights_hashes": True,
        "state_machine": [
            "DRAFT",
            "REVIEW",
            "AUTHORISED",
            "SUBMITTED",
            "SETTLED",
            "FAILED",
            "CANCELLED",
        ],
        "provider_calling": False,
        "journal_posting": False,
        "settlement_execution": False,
        "money_movement": False,
        "human_authority_final": True,
    }
