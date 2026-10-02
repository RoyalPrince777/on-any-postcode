"""Read-only multi-currency revaluation for SIKA accounting.

Calculates reporting-currency value and unrealised FX gain/loss from supplied
book and closing rates. It does not execute FX, mutate journals, or move money.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation


class RevaluationError(ValueError):
    """Raised when revaluation inputs are invalid."""


def _decimal(value: object, *, error: str, positive: bool = False) -> Decimal:
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise RevaluationError(error) from exc
    if not parsed.is_finite() or (positive and parsed <= 0):
        raise RevaluationError(error)
    return parsed


@dataclass(frozen=True)
class RevaluationResult:
    source_currency: str
    reporting_currency: str
    source_amount: Decimal
    book_rate: Decimal
    closing_rate: Decimal
    book_value_reporting: Decimal
    closing_value_reporting: Decimal
    unrealised_fx_gain_loss: Decimal
    human_review_required: bool
    fx_executed: bool = False
    ledger_modified: bool = False
    money_moved: bool = False

    def as_dict(self) -> dict[str, object]:
        return {
            "source_currency": self.source_currency,
            "reporting_currency": self.reporting_currency,
            "source_amount": f"{self.source_amount:.2f}",
            "book_rate": str(self.book_rate),
            "closing_rate": str(self.closing_rate),
            "book_value_reporting": f"{self.book_value_reporting:.2f}",
            "closing_value_reporting": f"{self.closing_value_reporting:.2f}",
            "unrealised_fx_gain_loss": f"{self.unrealised_fx_gain_loss:.2f}",
            "human_review_required": self.human_review_required,
            "fx_executed": self.fx_executed,
            "ledger_modified": self.ledger_modified,
            "money_moved": self.money_moved,
        }


def revalue(
    *,
    source_currency: object,
    reporting_currency: object,
    source_amount: object,
    book_rate: object,
    closing_rate: object,
) -> RevaluationResult:
    source = str(source_currency or "").strip().upper()
    reporting = str(reporting_currency or "").strip().upper()
    if not source:
        raise RevaluationError("source_currency_required")
    if not reporting:
        raise RevaluationError("reporting_currency_required")
    if source == reporting:
        raise RevaluationError("currencies_must_differ")

    amount = _decimal(source_amount, error="source_amount_invalid")
    if amount == 0:
        raise RevaluationError("source_amount_zero")
    book = _decimal(book_rate, error="book_rate_invalid", positive=True)
    closing = _decimal(closing_rate, error="closing_rate_invalid", positive=True)

    book_value = (amount * book).quantize(Decimal("0.01"))
    closing_value = (amount * closing).quantize(Decimal("0.01"))
    gain_loss = (closing_value - book_value).quantize(Decimal("0.01"))

    return RevaluationResult(
        source_currency=source,
        reporting_currency=reporting,
        source_amount=amount.quantize(Decimal("0.01")),
        book_rate=book,
        closing_rate=closing,
        book_value_reporting=book_value,
        closing_value_reporting=closing_value,
        unrealised_fx_gain_loss=gain_loss,
        human_review_required=gain_loss != 0,
        fx_executed=False,
        ledger_modified=False,
        money_moved=False,
    )


def status() -> dict[str, object]:
    return {
        "system": "SIKA Multi-Currency Revaluation",
        "first_party": True,
        "mode": "read_only_fx_valuation",
        "book_rate_supported": True,
        "closing_rate_supported": True,
        "unrealised_gain_loss_supported": True,
        "fx_execution": False,
        "ledger_mutation": False,
        "money_movement": False,
        "human_authority_final": True,
    }
