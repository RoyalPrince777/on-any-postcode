"""Deterministic first-party Financial Intelligence for OAP Banking.

This layer reads governed financial state and produces explainable risk signals.
It cannot approve transactions, move money, change ledger state, or override
Guardian/Human Authority.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from . import sika_treasury_controls


class FinancialIntelligenceError(ValueError):
    """Raised when financial intelligence inputs are invalid."""


def _non_negative(value: object, *, error: str) -> Decimal:
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise FinancialIntelligenceError(error) from exc
    if not parsed.is_finite() or parsed < 0:
        raise FinancialIntelligenceError(error)
    return parsed.quantize(Decimal("0.01"))


def _count(value: object, *, error: str) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise FinancialIntelligenceError(error) from exc
    if parsed < 0:
        raise FinancialIntelligenceError(error)
    return parsed


@dataclass(frozen=True)
class FinancialIntelligenceSnapshot:
    liquidity_state: str
    reserve_coverage_ratio: Decimal | None
    reconciliation_state: str
    provider_concentration_state: str
    jurisdiction_isolation_state: str
    human_review_required: bool
    execution_authorised: bool = False
    money_moved: bool = False

    def as_dict(self) -> dict[str, object]:
        return {
            "liquidity_state": self.liquidity_state,
            "reserve_coverage_ratio": (
                None
                if self.reserve_coverage_ratio is None
                else f"{self.reserve_coverage_ratio:.4f}"
            ),
            "reconciliation_state": self.reconciliation_state,
            "provider_concentration_state": self.provider_concentration_state,
            "jurisdiction_isolation_state": self.jurisdiction_isolation_state,
            "human_review_required": self.human_review_required,
            "execution_authorised": self.execution_authorised,
            "money_moved": self.money_moved,
        }


def assess(
    *,
    treasury: sika_treasury_controls.TreasurySnapshot,
    unreconciled_items: object = 0,
    active_provider_count: object = 0,
    largest_provider_share_percent: object = "0",
    jurisdiction_boundary_breaches: object = 0,
) -> FinancialIntelligenceSnapshot:
    """Produce explainable financial risk signals from supplied governed state."""

    unreconciled = _count(
        unreconciled_items,
        error="unreconciled_items_invalid",
    )
    providers = _count(
        active_provider_count,
        error="active_provider_count_invalid",
    )
    largest_share = _non_negative(
        largest_provider_share_percent,
        error="provider_share_invalid",
    )
    if largest_share > 100:
        raise FinancialIntelligenceError("provider_share_invalid")

    boundary_breaches = _count(
        jurisdiction_boundary_breaches,
        error="jurisdiction_boundary_breaches_invalid",
    )

    obligations = (
        treasury.committed_sika
        + treasury.tax_reserved_sika
        + treasury.operating_reserve_sika
    )
    reserve_coverage = (
        None
        if obligations == 0
        else (treasury.available_sika / obligations).quantize(Decimal("0.0001"))
    )

    if treasury.shortfall_sika > 0:
        liquidity_state = "SHORTFALL"
    elif reserve_coverage is None:
        liquidity_state = "NO_OBLIGATIONS"
    elif reserve_coverage < Decimal("1.10"):
        liquidity_state = "THIN_COVERAGE"
    else:
        liquidity_state = "HEALTHY"

    if unreconciled == 0:
        reconciliation_state = "CLEAR"
    elif unreconciled <= 5:
        reconciliation_state = "REVIEW"
    else:
        reconciliation_state = "ELEVATED"

    if providers == 0:
        provider_state = "NO_ACTIVE_PROVIDER"
    elif providers == 1 or largest_share >= Decimal(80):
        provider_state = "CONCENTRATED"
    elif largest_share >= Decimal(50):
        provider_state = "WATCH"
    else:
        provider_state = "DIVERSIFIED"

    jurisdiction_state = "CLEAR" if boundary_breaches == 0 else "BREACH"

    review_required = any(
        (
            liquidity_state in {"SHORTFALL", "THIN_COVERAGE"},
            reconciliation_state != "CLEAR",
            provider_state in {"NO_ACTIVE_PROVIDER", "CONCENTRATED"},
            jurisdiction_state == "BREACH",
        )
    )

    return FinancialIntelligenceSnapshot(
        liquidity_state=liquidity_state,
        reserve_coverage_ratio=reserve_coverage,
        reconciliation_state=reconciliation_state,
        provider_concentration_state=provider_state,
        jurisdiction_isolation_state=jurisdiction_state,
        human_review_required=review_required,
        execution_authorised=False,
        money_moved=False,
    )


def status() -> dict[str, object]:
    return {
        "system": "OAP Financial Intelligence",
        "first_party": True,
        "mode": "deterministic_read_only",
        "liquidity_intelligence": True,
        "reserve_coverage_intelligence": True,
        "reconciliation_exception_intelligence": True,
        "provider_concentration_intelligence": True,
        "jurisdiction_isolation_intelligence": True,
        "predictive_ai_controls_money": False,
        "execution_authority": False,
        "money_movement": False,
        "human_authority_final": True,
    }
