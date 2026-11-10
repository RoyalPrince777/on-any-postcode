"""Read-only Financial Statements Intelligence for SIKA.

Projects Balance Sheet, Profit & Loss, cash movement, and equity movement from
validated journal evidence and typed accounts. It does not file statutory
accounts, mutate the ledger, or move money.
"""
from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Decimal

from . import sika_double_entry


@dataclass(frozen=True)
class StatementSnapshot:
    assets: Decimal
    liabilities: Decimal
    equity: Decimal
    income: Decimal
    expenses: Decimal
    profit_or_loss: Decimal
    cash_movement: Decimal
    equity_movement: Decimal
    balance_sheet_balanced: bool
    human_review_required: bool
    statutory_accounts_generated: bool = False
    ledger_modified: bool = False
    money_moved: bool = False

    def as_dict(self) -> dict[str, object]:
        return {
            "assets": f"{self.assets:.2f}",
            "liabilities": f"{self.liabilities:.2f}",
            "equity": f"{self.equity:.2f}",
            "income": f"{self.income:.2f}",
            "expenses": f"{self.expenses:.2f}",
            "profit_or_loss": f"{self.profit_or_loss:.2f}",
            "cash_movement": f"{self.cash_movement:.2f}",
            "equity_movement": f"{self.equity_movement:.2f}",
            "balance_sheet_balanced": self.balance_sheet_balanced,
            "human_review_required": self.human_review_required,
            "statutory_accounts_generated": self.statutory_accounts_generated,
            "ledger_modified": self.ledger_modified,
            "money_moved": self.money_moved,
        }


def _account_balance(
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
                raise ValueError("account_currency_mismatch")
            if line.side is sika_double_entry.Side.DEBIT:
                debit += line.amount
            else:
                credit += line.amount

    if account.account_class in {
        sika_double_entry.AccountClass.ASSET,
        sika_double_entry.AccountClass.EXPENSE,
    }:
        return debit - credit
    return credit - debit


def project(
    *,
    accounts: Iterable[sika_double_entry.Account],
    journals: Iterable[sika_double_entry.JournalBatch],
    cash_account_ids: Iterable[str] = (),
) -> StatementSnapshot:
    account_list = tuple(accounts)
    journal_list = tuple(journals)
    cash_ids = {str(item).strip() for item in cash_account_ids if str(item).strip()}

    totals = {
        sika_double_entry.AccountClass.ASSET: Decimal("0.00"),
        sika_double_entry.AccountClass.LIABILITY: Decimal("0.00"),
        sika_double_entry.AccountClass.EQUITY: Decimal("0.00"),
        sika_double_entry.AccountClass.INCOME: Decimal("0.00"),
        sika_double_entry.AccountClass.EXPENSE: Decimal("0.00"),
    }
    cash_movement = Decimal("0.00")

    for account in account_list:
        balance = _account_balance(account, journal_list)
        totals[account.account_class] += balance
        if account.account_id in cash_ids:
            cash_movement += balance

    assets = totals[sika_double_entry.AccountClass.ASSET]
    liabilities = totals[sika_double_entry.AccountClass.LIABILITY]
    equity = totals[sika_double_entry.AccountClass.EQUITY]
    income = totals[sika_double_entry.AccountClass.INCOME]
    expenses = totals[sika_double_entry.AccountClass.EXPENSE]
    profit_or_loss = income - expenses
    equity_movement = equity + profit_or_loss

    balance_sheet_balanced = assets == liabilities + equity_movement

    return StatementSnapshot(
        assets=assets,
        liabilities=liabilities,
        equity=equity,
        income=income,
        expenses=expenses,
        profit_or_loss=profit_or_loss,
        cash_movement=cash_movement,
        equity_movement=equity_movement,
        balance_sheet_balanced=balance_sheet_balanced,
        human_review_required=not balance_sheet_balanced,
        statutory_accounts_generated=False,
        ledger_modified=False,
        money_moved=False,
    )


def status() -> dict[str, object]:
    return {
        "system": "OAP Financial Statements Intelligence",
        "first_party": True,
        "mode": "ledger_evidence_projection",
        "balance_sheet_projection": True,
        "profit_and_loss_projection": True,
        "cash_movement_projection": True,
        "equity_movement_projection": True,
        "statutory_accounts_generated": False,
        "filing_readiness_claimed": False,
        "ledger_mutation": False,
        "money_movement": False,
        "human_authority_final": True,
    }
