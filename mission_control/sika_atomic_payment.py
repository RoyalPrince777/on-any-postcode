"""Atomic SIKA payment creation with customer authority and value hold.

Creates one DRAFT payment intent, one hash-bound authority receipt and one
ACTIVE hold inside one PostgreSQL transaction. It serializes per payer account
with a row lock and refuses insufficient ledger-derived available balance.

This module does not authorize provider submission, settle funds, post journals,
or move money.
"""
from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any

from . import (
    postgres_db,
    sika_account_engine,
    sika_customer_payment_authority,
)


class AtomicPaymentError(ValueError):
    """Raised when an atomic customer payment cannot be created safely."""


class AtomicPaymentUnavailable(RuntimeError):
    """Raised when the atomic transaction cannot be completed durably."""


def _required(value: object, field: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise AtomicPaymentError(f"{field}_required")
    return text


def _amount(value: object) -> Decimal:
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise AtomicPaymentError("payment_amount_invalid") from exc
    if not parsed.is_finite() or parsed <= 0:
        raise AtomicPaymentError("payment_amount_invalid")
    return parsed.quantize(Decimal("0.01"))


def create(
    *,
    payer_account: sika_account_engine.BankAccount,
    payment_id: object,
    hold_id: object,
    idempotency_key: object,
    payee_reference: object,
    amount: object,
    currency: object,
    jurisdiction: object,
    authority_reference: object,
    authorised_at: object,
    expires_at: object,
) -> dict[str, Any]:
    if not isinstance(payer_account, sika_account_engine.BankAccount):
        raise AtomicPaymentError("payer_account_required")
    if not payer_account.customer_activity_allowed:
        raise AtomicPaymentError("payer_account_not_open")

    payment_id_value = _required(payment_id, "payment_id")
    hold_id_value = _required(hold_id, "hold_id")
    idempotency_value = _required(idempotency_key, "idempotency_key")
    payee_value = _required(payee_reference, "payee_reference")
    amount_value = _amount(amount)
    currency_value = _required(currency, "currency").upper()
    jurisdiction_value = _required(jurisdiction, "jurisdiction")

    if currency_value != payer_account.currency:
        raise AtomicPaymentError("payer_currency_mismatch")
    if jurisdiction_value != payer_account.jurisdiction:
        raise AtomicPaymentError("payer_jurisdiction_mismatch")

    receipt = sika_customer_payment_authority.build_receipt(
        payment_id=payment_id_value,
        payer_account_id=payer_account.account_id,
        payee_reference=payee_value,
        amount=f"{amount_value:.2f}",
        currency=currency_value,
        jurisdiction=jurisdiction_value,
        authority_reference=_required(authority_reference, "authority_reference"),
        authorised_at=_required(authorised_at, "authorised_at"),
        expires_at=_required(expires_at, "expires_at"),
    )

    try:
        with postgres_db.connect() as connection:
            locked = connection.execute(
                """SELECT account_id,status,ledger_account_id,currency,jurisdiction
                   FROM oap_sika_accounts
                   WHERE account_id=%s
                   FOR UPDATE""",
                (payer_account.account_id,),
            ).fetchone()
            if locked is None:
                raise AtomicPaymentError("payer_account_not_found")
            if str(locked[1]) != "OPEN":
                raise AtomicPaymentError("payer_account_not_open")
            if str(locked[2]) != payer_account.ledger_account_id:
                raise AtomicPaymentError("payer_ledger_binding_changed")
            if str(locked[3]) != currency_value:
                raise AtomicPaymentError("payer_currency_mismatch")
            if str(locked[4]) != jurisdiction_value:
                raise AtomicPaymentError("payer_jurisdiction_mismatch")

            journal = connection.execute(
                """SELECT
                       COALESCE(SUM(CASE WHEN side='credit' THEN amount ELSE 0 END),0),
                       COALESCE(SUM(CASE WHEN side='debit' THEN amount ELSE 0 END),0)
                   FROM oap_sika_journal_lines
                   WHERE account_id=%s AND currency=%s""",
                (payer_account.ledger_account_id, currency_value),
            ).fetchone()
            active_holds = connection.execute(
                """SELECT COALESCE(SUM(amount),0)
                   FROM oap_sika_payment_holds
                   WHERE payer_account_id=%s
                     AND currency=%s
                     AND status='ACTIVE'""",
                (payer_account.account_id, currency_value),
            ).fetchone()

            credits = Decimal(str(journal[0] or "0"))
            debits = Decimal(str(journal[1] or "0"))
            reserved = Decimal(str(active_holds[0] or "0"))
            available = credits - debits - reserved
            if available < amount_value:
                raise AtomicPaymentError("insufficient_available_balance")

            connection.execute(
                """INSERT INTO oap_sika_payment_intents(
                       payment_id,idempotency_key,payer_account_id,payee_reference,
                       amount,currency,jurisdiction,status
                   ) VALUES (%s,%s,%s,%s,%s,%s,%s,'DRAFT')""",
                (
                    payment_id_value,
                    idempotency_value,
                    payer_account.account_id,
                    payee_value,
                    amount_value,
                    currency_value,
                    jurisdiction_value,
                ),
            )
            connection.execute(
                """INSERT INTO oap_sika_customer_payment_authority(
                       receipt_hash,payment_id,payer_account_id,payee_reference,
                       amount,currency,jurisdiction,authority_reference,
                       authorised_at,expires_at,revoked
                   ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,FALSE)""",
                (
                    receipt["receipt_hash"],
                    payment_id_value,
                    payer_account.account_id,
                    payee_value,
                    f"{amount_value:.2f}",
                    currency_value,
                    jurisdiction_value,
                    receipt["authority_reference"],
                    receipt["authorised_at"],
                    receipt["expires_at"],
                ),
            )
            connection.execute(
                """INSERT INTO oap_sika_payment_holds(
                       hold_id,payment_id,payer_account_id,amount,currency,status
                   ) VALUES (%s,%s,%s,%s,%s,'ACTIVE')""",
                (
                    hold_id_value,
                    payment_id_value,
                    payer_account.account_id,
                    amount_value,
                    currency_value,
                ),
            )
            connection.commit()
    except AtomicPaymentError:
        raise
    except Exception as exc:
        raise AtomicPaymentUnavailable("atomic_payment_create_failed") from exc

    return {
        "payment_id": payment_id_value,
        "hold_id": hold_id_value,
        "payer_account_id": payer_account.account_id,
        "amount": f"{amount_value:.2f}",
        "currency": currency_value,
        "jurisdiction": jurisdiction_value,
        "payment_status": "DRAFT",
        "hold_status": "ACTIVE",
        "customer_authority_receipt_hash": receipt["receipt_hash"],
        "atomic": True,
        "provider_calling": False,
        "settlement_execution": False,
        "money_movement": False,
        "human_authority_final": True,
    }


def status() -> dict[str, object]:
    return {
        "system": "SIKA Atomic Payment Creation",
        "first_party": True,
        "single_database_transaction": True,
        "payer_account_row_lock": True,
        "ledger_balance_checked": True,
        "active_holds_checked": True,
        "insufficient_balance_fails_closed": True,
        "payment_intent_created": True,
        "authority_receipt_persisted": True,
        "payment_hold_created": True,
        "partial_commit_allowed": False,
        "provider_calling": False,
        "journal_posting": False,
        "settlement_execution": False,
        "money_movement": False,
        "human_authority_final": True,
    }
