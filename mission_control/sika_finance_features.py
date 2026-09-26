"""SIKA rewards, trust and deferred-payment planning.

All outputs are advisory/non-executable. Cashback is only created from an
explicit funded reward pool. Deferred-payment plans are previews and never
create credit agreements.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP


class FinanceFeatureError(ValueError):
    pass


def _money(value: object) -> Decimal:
    amount = Decimal(str(value))
    if amount < 0:
        raise FinanceFeatureError("amount_must_not_be_negative")
    return amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class CashbackQuote:
    purchase_sika: Decimal
    rate_percent: Decimal
    reward_sika: Decimal
    funded_pool_available_sika: Decimal
    executable: bool = False

    def as_dict(self) -> dict[str, str | bool]:
        return {
            "purchase_sika": f"{self.purchase_sika:.2f}",
            "rate_percent": f"{self.rate_percent:.2f}",
            "reward_sika": f"{self.reward_sika:.2f}",
            "funded_pool_available_sika": f"{self.funded_pool_available_sika:.2f}",
            "funded": self.reward_sika <= self.funded_pool_available_sika,
            "executable": self.executable,
        }


def cashback_quote(
    purchase_sika: object,
    rate_percent: object,
    *,
    funded_pool_available_sika: object,
) -> CashbackQuote:
    purchase = _money(purchase_sika)
    rate = Decimal(str(rate_percent))
    pool = _money(funded_pool_available_sika)
    if rate < 0 or rate > 100:
        raise FinanceFeatureError("cashback_rate_out_of_range")
    reward = (purchase * rate / Decimal(100)).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )
    return CashbackQuote(purchase, rate, reward, pool)


def deferred_payment_preview(
    purchase_sika: object,
    instalments: object,
    *,
    monthly_disposable_sika: object | None = None,
) -> dict[str, object]:
    purchase = _money(purchase_sika)
    try:
        count = int(instalments)
    except (TypeError, ValueError) as exc:
        raise FinanceFeatureError("invalid_instalment_count") from exc
    if count < 2 or count > 12:
        raise FinanceFeatureError("instalments_must_be_between_2_and_12")
    each = (purchase / count).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    schedule = []
    remaining = purchase
    for number in range(1, count + 1):
        payment = each if number < count else remaining
        remaining -= payment
        schedule.append({"number": number, "amount_sika": f"{payment:.2f}"})

    affordability = "not_assessed"
    disposable = None
    if monthly_disposable_sika is not None:
        disposable = _money(monthly_disposable_sika)
        affordability = "within_input_limit" if each <= disposable else "review_required"

    return {
        "purchase_sika": f"{purchase:.2f}",
        "instalments": count,
        "schedule": schedule,
        "monthly_disposable_sika": None if disposable is None else f"{disposable:.2f}",
        "affordability_signal": affordability,
        "credit_agreement_created": False,
        "money_moved": False,
        "human_review_available": True,
        "executable": False,
    }


def trust_score_preview(
    *,
    payment_reliability: object,
    cashflow_resilience: object,
    account_stability: object,
    identity_confidence: object,
) -> dict[str, object]:
    factors = {
        "payment_reliability": Decimal(str(payment_reliability)),
        "cashflow_resilience": Decimal(str(cashflow_resilience)),
        "account_stability": Decimal(str(account_stability)),
        "identity_confidence": Decimal(str(identity_confidence)),
    }
    if any(value < 0 or value > 100 for value in factors.values()):
        raise FinanceFeatureError("score_factor_out_of_range")

    weighted = (
        factors["payment_reliability"] * Decimal("0.35")
        + factors["cashflow_resilience"] * Decimal("0.30")
        + factors["account_stability"] * Decimal("0.20")
        + factors["identity_confidence"] * Decimal("0.15")
    )
    score = int((weighted * Decimal(10)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    return {
        "score": score,
        "scale": 1000,
        "factors": {key: f"{value:.1f}" for key, value in factors.items()},
        "why": [
            "Payment reliability carries 35% of this preview.",
            "Cash-flow resilience carries 30% of this preview.",
            "Account stability carries 20% of this preview.",
            "Identity confidence carries 15% of this preview.",
        ],
        "credit_decision": False,
        "human_review_available": True,
        "executable": False,
    }
