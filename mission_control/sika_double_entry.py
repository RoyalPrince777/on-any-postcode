"""First-party SIKA double-entry accounting core.

This module validates immutable journal batches before any persistence layer.
Every batch must balance by currency. It does not settle payments, mutate
external accounts or create customer funds.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from enum import StrEnum


class LedgerError(ValueError):
    """Raised when a journal batch violates accounting invariants."""


class Side(StrEnum):
    DEBIT = "debit"
    CREDIT = "credit"


class AccountClass(StrEnum):
    ASSET = "asset"
    LIABILITY = "liability"
    EQUITY = "equity"
    INCOME = "income"
    EXPENSE = "expense"


@dataclass(frozen=True)
class Account:
    account_id: str
    name: str
    account_class: AccountClass
    currency: str
    jurisdiction: str


@dataclass(frozen=True)
class JournalLine:
    account_id: str
    side: Side
    amount: Decimal
    currency: str


@dataclass(frozen=True)
class JournalBatch:
    journal_id: str
    reference: str
    lines: tuple[JournalLine, ...]
    balanced: bool
    posted: bool = False

    def as_dict(self) -> dict[str, object]:
        return {
            "journal_id": self.journal_id,
            "reference": self.reference,
            "balanced": self.balanced,
            "posted": self.posted,
            "lines": [
                {
                    "account_id": line.account_id,
                    "side": line.side.value,
                    "amount": f"{line.amount:.2f}",
                    "currency": line.currency,
                }
                for line in self.lines
            ],
        }


def _clean_text(value: object, *, error: str) -> str:
    cleaned = str(value or "").strip()
    if not cleaned:
        raise LedgerError(error)
    return cleaned


def _amount(value: object) -> Decimal:
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise LedgerError("journal_amount_invalid") from exc
    if not parsed.is_finite() or parsed <= 0:
        raise LedgerError("journal_amount_invalid")
    return parsed.quantize(Decimal("0.01"))


def account(
    *,
    account_id: object,
    name: object,
    account_class: AccountClass | str,
    currency: object,
    jurisdiction: object,
) -> Account:
    try:
        klass = AccountClass(account_class)
    except ValueError as exc:
        raise LedgerError("account_class_invalid") from exc
    return Account(
        account_id=_clean_text(account_id, error="account_id_required"),
        name=_clean_text(name, error="account_name_required"),
        account_class=klass,
        currency=_clean_text(currency, error="account_currency_required").upper(),
        jurisdiction=_clean_text(
            jurisdiction,
            error="account_jurisdiction_required",
        ),
    )


def line(
    *,
    account_id: object,
    side: Side | str,
    amount: object,
    currency: object,
) -> JournalLine:
    try:
        parsed_side = Side(side)
    except ValueError as exc:
        raise LedgerError("journal_side_invalid") from exc
    return JournalLine(
        account_id=_clean_text(account_id, error="journal_account_required"),
        side=parsed_side,
        amount=_amount(amount),
        currency=_clean_text(currency, error="journal_currency_required").upper(),
    )


def validate_batch(
    *,
    journal_id: object,
    reference: object,
    lines: tuple[JournalLine, ...] | list[JournalLine],
) -> JournalBatch:
    journal_id_value = _clean_text(journal_id, error="journal_id_required")
    reference_value = _clean_text(reference, error="journal_reference_required")
    batch_lines = tuple(lines)

    if len(batch_lines) < 2:
        raise LedgerError("journal_requires_at_least_two_lines")

    currencies = {item.currency for item in batch_lines}
    for currency in currencies:
        debit = sum(
            (item.amount for item in batch_lines if item.currency == currency and item.side is Side.DEBIT),
            Decimal("0.00"),
        )
        credit = sum(
            (item.amount for item in batch_lines if item.currency == currency and item.side is Side.CREDIT),
            Decimal("0.00"),
        )
        if debit != credit:
            raise LedgerError("journal_not_balanced")

    return JournalBatch(
        journal_id=journal_id_value,
        reference=reference_value,
        lines=batch_lines,
        balanced=True,
        posted=False,
    )


def reversal_batch(
    *,
    original: JournalBatch,
    journal_id: object,
    reference: object,
) -> JournalBatch:
    """Create a compensating journal without mutating the original batch."""

    reversed_lines = tuple(
        JournalLine(
            account_id=item.account_id,
            side=Side.CREDIT if item.side is Side.DEBIT else Side.DEBIT,
            amount=item.amount,
            currency=item.currency,
        )
        for item in original.lines
    )
    return validate_batch(
        journal_id=journal_id,
        reference=reference,
        lines=reversed_lines,
    )


def status() -> dict[str, object]:
    return {
        "system": "SIKA Double-Entry Core",
        "first_party": True,
        "validates_debits_and_credits": True,
        "balances_per_currency": True,
        "supports_account_classes": True,
        "supports_compensating_reversals": True,
        "persistent_journal_store": False,
        "settlement_execution": False,
        "external_money_movement": False,
        "human_authority_final": True,
    }
