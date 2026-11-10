"""SIKA period closing and retained-earnings engine.

Builds balanced closing journals from validated income/expense activity after
the accounting period is CLOSED. It never edits source journals, posts to a
provider, generates statutory accounts, or moves money.
"""
from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Decimal

from . import sika_accounting_controls, sika_double_entry


class ClosingError(ValueError):
    """Raised when a closing operation violates accounting controls."""


@dataclass(frozen=True)
class PeriodCloseResult:
    period_id: str
    jurisdiction: str
    profit_or_loss: Decimal
    closing_batch: sika_double_entry.JournalBatch
    retained_earnings_account_id: str
    source_journals_modified: bool = False
    money_moved: bool = False

    def as_dict(self) -> dict[str, object]:
        return {
            "period_id": self.period_id,
            "jurisdiction": self.jurisdiction,
            "profit_or_loss": f"{self.profit_or_loss:.2f}",
            "closing_batch": self.closing_batch.as_dict(),
            "retained_earnings_account_id": self.retained_earnings_account_id,
            "source_journals_modified": self.source_journals_modified,
            "money_moved": self.money_moved,
        }


def _net_balance(
    *,
    account: sika_double_entry.Account,
    journals: Iterable[sika_double_entry.JournalBatch],
) -> Decimal:
    debit = Decimal("0.00")
    credit = Decimal("0.00")
    for batch in journals:
        for line in batch.lines:
            if line.account_id != account.account_id:
                continue
            if line.currency != account.currency:
                raise ClosingError("account_currency_mismatch")
            if line.side is sika_double_entry.Side.DEBIT:
                debit += line.amount
            else:
                credit += line.amount
    if account.account_class is sika_double_entry.AccountClass.INCOME:
        return credit - debit
    if account.account_class is sika_double_entry.AccountClass.EXPENSE:
        return debit - credit
    raise ClosingError("closing_account_must_be_income_or_expense")


def build_close(
    *,
    period: sika_accounting_controls.PeriodState,
    accounts: Iterable[sika_double_entry.Account],
    journals: Iterable[sika_double_entry.JournalBatch],
    retained_earnings_account_id: str,
    closing_journal_id: str,
    reference: str,
) -> PeriodCloseResult:
    """Create a balanced closing batch for a CLOSED accounting period."""

    if period.status != "CLOSED":
        raise ClosingError("accounting_period_must_be_closed")

    account_list = tuple(accounts)
    journal_list = tuple(journals)
    retained = next(
        (item for item in account_list if item.account_id == retained_earnings_account_id),
        None,
    )
    if retained is None:
        raise ClosingError("retained_earnings_account_not_found")
    if retained.account_class is not sika_double_entry.AccountClass.EQUITY:
        raise ClosingError("retained_earnings_account_must_be_equity")
    if retained.jurisdiction != period.jurisdiction:
        raise ClosingError("retained_earnings_jurisdiction_mismatch")

    lines: list[sika_double_entry.JournalLine] = []
    total_income = Decimal("0.00")
    total_expense = Decimal("0.00")

    for account in account_list:
        if account.jurisdiction != period.jurisdiction:
            continue
        if account.account_class not in {
            sika_double_entry.AccountClass.INCOME,
            sika_double_entry.AccountClass.EXPENSE,
        }:
            continue

        balance = _net_balance(account=account, journals=journal_list)
        if balance == 0:
            continue

        if account.account_class is sika_double_entry.AccountClass.INCOME:
            if balance < 0:
                raise ClosingError("income_account_abnormal_balance")
            total_income += balance
            lines.append(
                sika_double_entry.line(
                    account_id=account.account_id,
                    side="debit",
                    amount=balance,
                    currency=account.currency,
                )
            )
        else:
            if balance < 0:
                raise ClosingError("expense_account_abnormal_balance")
            total_expense += balance
            lines.append(
                sika_double_entry.line(
                    account_id=account.account_id,
                    side="credit",
                    amount=balance,
                    currency=account.currency,
                )
            )

    profit_or_loss = total_income - total_expense
    if profit_or_loss > 0:
        lines.append(
            sika_double_entry.line(
                account_id=retained.account_id,
                side="credit",
                amount=profit_or_loss,
                currency=retained.currency,
            )
        )
    elif profit_or_loss < 0:
        lines.append(
            sika_double_entry.line(
                account_id=retained.account_id,
                side="debit",
                amount=abs(profit_or_loss),
                currency=retained.currency,
            )
        )
    else:
        raise ClosingError("period_has_no_closeable_profit_or_loss")

    batch = sika_double_entry.validate_batch(
        journal_id=closing_journal_id,
        reference=reference,
        lines=lines,
    )
    return PeriodCloseResult(
        period_id=period.period_id,
        jurisdiction=period.jurisdiction,
        profit_or_loss=profit_or_loss,
        closing_batch=batch,
        retained_earnings_account_id=retained.account_id,
        source_journals_modified=False,
        money_moved=False,
    )


def status() -> dict[str, object]:
    return {
        "system": "SIKA Closing + Retained Earnings",
        "first_party": True,
        "requires_closed_period": True,
        "income_close": True,
        "expense_close": True,
        "retained_earnings_transfer": True,
        "balanced_closing_batch": True,
        "source_journal_mutation": False,
        "statutory_accounts_generated": False,
        "settlement_execution": False,
        "money_movement": False,
        "human_authority_final": True,
    }
