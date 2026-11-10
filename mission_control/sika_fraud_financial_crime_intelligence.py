"""Read-only Fraud and Financial-Crime Intelligence for SIKA.

Produces deterministic review signals from supplied transaction/settlement
facts. It cannot freeze funds, reject payments, mutate ledgers, file reports,
or move money.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation


class FraudIntelligenceError(ValueError):
    """Raised when fraud-intelligence inputs are invalid."""


def _amount(value: object, *, error: str) -> Decimal:
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise FraudIntelligenceError(error) from exc
    if not parsed.is_finite() or parsed < 0:
        raise FraudIntelligenceError(error)
    return parsed.quantize(Decimal("0.01"))


def _count(value: object, *, error: str) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise FraudIntelligenceError(error) from exc
    if parsed < 0:
        raise FraudIntelligenceError(error)
    return parsed


@dataclass(frozen=True)
class FraudFinancialCrimeSnapshot:
    velocity_state: str
    amount_state: str
    failed_settlement_state: str
    jurisdiction_state: str
    provider_reference_state: str
    reconciliation_state: str
    risk_level: str
    human_review_required: bool
    autonomous_block: bool = False
    regulatory_report_filed: bool = False
    money_moved: bool = False

    def as_dict(self) -> dict[str, object]:
        return {
            "velocity_state": self.velocity_state,
            "amount_state": self.amount_state,
            "failed_settlement_state": self.failed_settlement_state,
            "jurisdiction_state": self.jurisdiction_state,
            "provider_reference_state": self.provider_reference_state,
            "reconciliation_state": self.reconciliation_state,
            "risk_level": self.risk_level,
            "human_review_required": self.human_review_required,
            "autonomous_block": self.autonomous_block,
            "regulatory_report_filed": self.regulatory_report_filed,
            "money_moved": self.money_moved,
        }


def assess(
    *,
    transactions_last_hour: object,
    baseline_hourly_transactions: object,
    transaction_amount: object,
    baseline_amount: object,
    failed_settlements_24h: object = 0,
    jurisdiction_mismatch: bool = False,
    provider_reference_reused: bool = False,
    reconciliation_exception: bool = False,
) -> FraudFinancialCrimeSnapshot:
    """Produce explainable review signals without taking financial action."""

    tx_hour = _count(
        transactions_last_hour,
        error="transactions_last_hour_invalid",
    )
    baseline_tx = _count(
        baseline_hourly_transactions,
        error="baseline_hourly_transactions_invalid",
    )
    amount = _amount(transaction_amount, error="transaction_amount_invalid")
    baseline = _amount(baseline_amount, error="baseline_amount_invalid")
    failed = _count(
        failed_settlements_24h,
        error="failed_settlements_24h_invalid",
    )

    velocity_state = (
        "SPIKE"
        if baseline_tx > 0 and tx_hour >= max(10, baseline_tx * 4)
        else "NORMAL"
    )
    amount_state = (
        "ANOMALOUS"
        if baseline > 0 and amount >= baseline * 5
        else "NORMAL"
    )
    failed_state = "ELEVATED" if failed >= 3 else "NORMAL"
    jurisdiction_state = "MISMATCH" if jurisdiction_mismatch else "CLEAR"
    reference_state = "REUSED" if provider_reference_reused else "UNIQUE"
    reconciliation_state = "EXCEPTION" if reconciliation_exception else "CLEAR"

    signals = sum(
        (
            velocity_state == "SPIKE",
            amount_state == "ANOMALOUS",
            failed_state == "ELEVATED",
            jurisdiction_state == "MISMATCH",
            reference_state == "REUSED",
            reconciliation_state == "EXCEPTION",
        )
    )

    if signals >= 3:
        risk = "HIGH"
    elif signals >= 1:
        risk = "REVIEW"
    else:
        risk = "LOW"

    return FraudFinancialCrimeSnapshot(
        velocity_state=velocity_state,
        amount_state=amount_state,
        failed_settlement_state=failed_state,
        jurisdiction_state=jurisdiction_state,
        provider_reference_state=reference_state,
        reconciliation_state=reconciliation_state,
        risk_level=risk,
        human_review_required=risk != "LOW",
        autonomous_block=False,
        regulatory_report_filed=False,
        money_moved=False,
    )


def status() -> dict[str, object]:
    return {
        "system": "OAP Fraud + Financial-Crime Intelligence",
        "first_party": True,
        "mode": "deterministic_read_only",
        "velocity_signals": True,
        "amount_anomaly_signals": True,
        "failed_settlement_signals": True,
        "jurisdiction_mismatch_signals": True,
        "provider_reference_reuse_signals": True,
        "reconciliation_exception_signals": True,
        "autonomous_blocking": False,
        "regulatory_reporting_execution": False,
        "ledger_mutation": False,
        "money_movement": False,
        "human_authority_final": True,
    }
