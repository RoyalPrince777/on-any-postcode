"""Read-only runtime reconciliation for SIKA settlement evidence.

Matches a provider settlement receipt against an already-posted journal batch.
It does not call providers, alter journals, settle funds, or retry payments.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from . import sika_double_entry


class ReconciliationError(ValueError):
    """Raised when reconciliation evidence is malformed."""


def _required(value: object, *, error: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ReconciliationError(error)
    return text


def _amount(value: object) -> Decimal:
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ReconciliationError("settlement_amount_invalid") from exc
    if not parsed.is_finite() or parsed <= 0:
        raise ReconciliationError("settlement_amount_invalid")
    return parsed.quantize(Decimal("0.01"))


@dataclass(frozen=True)
class SettlementReceipt:
    provider_id: str
    provider_reference: str
    journal_reference: str
    amount: Decimal
    currency: str
    settlement_status: str
    evidence_hash: str


@dataclass(frozen=True)
class ReconciliationResult:
    state: str
    reference_match: bool
    amount_match: bool
    currency_match: bool
    settlement_final: bool
    human_review_required: bool
    journal_modified: bool = False
    money_moved: bool = False

    def as_dict(self) -> dict[str, object]:
        return {
            "state": self.state,
            "reference_match": self.reference_match,
            "amount_match": self.amount_match,
            "currency_match": self.currency_match,
            "settlement_final": self.settlement_final,
            "human_review_required": self.human_review_required,
            "journal_modified": self.journal_modified,
            "money_moved": self.money_moved,
        }


def receipt(
    *,
    provider_id: object,
    provider_reference: object,
    journal_reference: object,
    amount: object,
    currency: object,
    settlement_status: object,
    evidence_hash: object,
) -> SettlementReceipt:
    status = _required(settlement_status, error="settlement_status_required").upper()
    if status not in {"PENDING", "SETTLED", "FAILED", "REVERSED"}:
        raise ReconciliationError("settlement_status_invalid")
    return SettlementReceipt(
        provider_id=_required(provider_id, error="provider_id_required"),
        provider_reference=_required(
            provider_reference,
            error="provider_reference_required",
        ),
        journal_reference=_required(
            journal_reference,
            error="journal_reference_required",
        ),
        amount=_amount(amount),
        currency=_required(currency, error="settlement_currency_required").upper(),
        settlement_status=status,
        evidence_hash=_required(evidence_hash, error="settlement_evidence_hash_required"),
    )


def reconcile(
    *,
    journal: sika_double_entry.JournalBatch,
    settlement: SettlementReceipt,
) -> ReconciliationResult:
    """Compare settlement evidence with the journal without mutating either."""

    currencies = {line.currency for line in journal.lines}
    amounts_by_currency: dict[str, Decimal] = {}
    for currency in currencies:
        debit_total = sum(
            (
                line.amount
                for line in journal.lines
                if line.currency == currency
                and line.side is sika_double_entry.Side.DEBIT
            ),
            Decimal("0.00"),
        )
        amounts_by_currency[currency] = debit_total

    reference_match = journal.reference == settlement.journal_reference
    currency_match = settlement.currency in amounts_by_currency
    amount_match = (
        currency_match
        and amounts_by_currency[settlement.currency] == settlement.amount
    )
    settlement_final = settlement.settlement_status == "SETTLED"

    if all((reference_match, currency_match, amount_match, settlement_final)):
        state = "MATCHED"
    elif settlement.settlement_status == "PENDING":
        state = "PENDING"
    elif settlement.settlement_status in {"FAILED", "REVERSED"}:
        state = "EXCEPTION"
    else:
        state = "MISMATCH"

    return ReconciliationResult(
        state=state,
        reference_match=reference_match,
        amount_match=bool(amount_match),
        currency_match=currency_match,
        settlement_final=settlement_final,
        human_review_required=state != "MATCHED",
        journal_modified=False,
        money_moved=False,
    )


def status() -> dict[str, object]:
    return {
        "system": "SIKA Runtime Reconciliation",
        "first_party": True,
        "mode": "read_only_match_engine",
        "matches_reference": True,
        "matches_amount": True,
        "matches_currency": True,
        "requires_final_settlement": True,
        "automatic_retry": False,
        "journal_mutation": False,
        "settlement_execution": False,
        "money_movement": False,
        "human_authority_final": True,
    }
