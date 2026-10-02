"""Read-only Accounting Intelligence for OAP Banking.

Consumes validated SIKA accounts and journal batches to produce explainable
accounting-control signals. It does not post journals, close periods, generate
statutory accounts, or move money.
"""
from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Decimal

from . import sika_double_entry


@dataclass(frozen=True)
class AccountingIntelligenceSnapshot:
    trial_balance_state: str
    chart_mapping_state: str
    suspense_state: str
    period_control_state: str
    reversal_state: str
    statement_readiness: str
    human_review_required: bool
    books_modified: bool = False
    money_moved: bool = False

    def as_dict(self) -> dict[str, object]:
        return {
            "trial_balance_state": self.trial_balance_state,
            "chart_mapping_state": self.chart_mapping_state,
            "suspense_state": self.suspense_state,
            "period_control_state": self.period_control_state,
            "reversal_state": self.reversal_state,
            "statement_readiness": self.statement_readiness,
            "human_review_required": self.human_review_required,
            "books_modified": self.books_modified,
            "money_moved": self.money_moved,
        }


def assess(
    *,
    accounts: Iterable[sika_double_entry.Account],
    journals: Iterable[sika_double_entry.JournalBatch],
    suspense_account_ids: Iterable[str] = (),
    closed_period_write_attempts: int = 0,
    unmatched_reversal_count: int = 0,
) -> AccountingIntelligenceSnapshot:
    """Assess structural accounting health without mutating the books."""

    if closed_period_write_attempts < 0:
        raise ValueError("closed_period_write_attempts_invalid")
    if unmatched_reversal_count < 0:
        raise ValueError("unmatched_reversal_count_invalid")

    account_map = {item.account_id: item for item in accounts}
    suspense_ids = {str(item).strip() for item in suspense_account_ids if str(item).strip()}
    batches = tuple(journals)

    currency_debits: dict[str, Decimal] = {}
    currency_credits: dict[str, Decimal] = {}
    unmapped_accounts: set[str] = set()
    suspense_amount = Decimal("0.00")

    for batch in batches:
        if not batch.balanced:
            trial_balance_state = "UNBALANCED"
            break
        for line in batch.lines:
            if line.account_id not in account_map:
                unmapped_accounts.add(line.account_id)
            if line.account_id in suspense_ids:
                suspense_amount += line.amount
            target = (
                currency_debits if line.side is sika_double_entry.Side.DEBIT
                else currency_credits
            )
            target[line.currency] = target.get(line.currency, Decimal("0.00")) + line.amount
    else:
        currencies = set(currency_debits) | set(currency_credits)
        trial_balance_state = (
            "BALANCED"
            if all(
                currency_debits.get(currency, Decimal("0.00"))
                == currency_credits.get(currency, Decimal("0.00"))
                for currency in currencies
            )
            else "UNBALANCED"
        )

    chart_mapping_state = "COMPLETE" if not unmapped_accounts else "UNMAPPED_ACCOUNTS"
    suspense_state = "CLEAR" if suspense_amount == 0 else "EXPOSURE"
    period_control_state = (
        "CLEAR" if closed_period_write_attempts == 0 else "VIOLATION"
    )
    reversal_state = "CLEAR" if unmatched_reversal_count == 0 else "UNMATCHED"

    statement_ready = all(
        (
            trial_balance_state == "BALANCED",
            chart_mapping_state == "COMPLETE",
            suspense_state == "CLEAR",
            period_control_state == "CLEAR",
            reversal_state == "CLEAR",
        )
    )

    return AccountingIntelligenceSnapshot(
        trial_balance_state=trial_balance_state,
        chart_mapping_state=chart_mapping_state,
        suspense_state=suspense_state,
        period_control_state=period_control_state,
        reversal_state=reversal_state,
        statement_readiness="STRUCTURALLY_READY" if statement_ready else "REVIEW_REQUIRED",
        human_review_required=not statement_ready,
        books_modified=False,
        money_moved=False,
    )


def status() -> dict[str, object]:
    return {
        "system": "OAP Accounting Intelligence",
        "first_party": True,
        "mode": "deterministic_read_only",
        "trial_balance_intelligence": True,
        "chart_of_accounts_mapping": True,
        "suspense_exposure_intelligence": True,
        "period_control_intelligence": True,
        "reversal_integrity_intelligence": True,
        "financial_statement_readiness": True,
        "statutory_accounts_generated": False,
        "books_mutated": False,
        "execution_authority": False,
        "money_movement": False,
        "human_authority_final": True,
    }
