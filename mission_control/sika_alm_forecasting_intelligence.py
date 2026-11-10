"""Read-only Asset-Liability Management forecasting for SIKA.

Projects forward liquidity pressure from a current treasury snapshot and
supplied maturity cash-flow buckets. It never moves funds, changes reserves,
executes hedges, or authorises treasury action.
"""
from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from . import sika_treasury_controls


class ALMForecastError(ValueError):
    """Raised when ALM forecasting inputs are invalid."""


def _amount(value: object, *, error: str) -> Decimal:
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ALMForecastError(error) from exc
    if not parsed.is_finite() or parsed < 0:
        raise ALMForecastError(error)
    return parsed.quantize(Decimal("0.01"))


@dataclass(frozen=True)
class MaturityBucket:
    label: str
    inflows_sika: Decimal
    outflows_sika: Decimal

    @property
    def net_sika(self) -> Decimal:
        return self.inflows_sika - self.outflows_sika


@dataclass(frozen=True)
class ALMForecastSnapshot:
    starting_free_liquidity_sika: Decimal
    projected_free_liquidity_sika: Decimal
    minimum_projected_liquidity_sika: Decimal
    cumulative_net_flow_sika: Decimal
    maturity_pressure_state: str
    reserve_trajectory_state: str
    concentration_state: str
    human_review_required: bool
    treasury_action_authorised: bool = False
    money_moved: bool = False

    def as_dict(self) -> dict[str, object]:
        return {
            "starting_free_liquidity_sika": f"{self.starting_free_liquidity_sika:.2f}",
            "projected_free_liquidity_sika": f"{self.projected_free_liquidity_sika:.2f}",
            "minimum_projected_liquidity_sika": f"{self.minimum_projected_liquidity_sika:.2f}",
            "cumulative_net_flow_sika": f"{self.cumulative_net_flow_sika:.2f}",
            "maturity_pressure_state": self.maturity_pressure_state,
            "reserve_trajectory_state": self.reserve_trajectory_state,
            "concentration_state": self.concentration_state,
            "human_review_required": self.human_review_required,
            "treasury_action_authorised": self.treasury_action_authorised,
            "money_moved": self.money_moved,
        }


def bucket(*, label: object, inflows_sika: object = "0", outflows_sika: object = "0") -> MaturityBucket:
    name = str(label or "").strip()
    if not name:
        raise ALMForecastError("maturity_bucket_label_required")
    return MaturityBucket(
        label=name,
        inflows_sika=_amount(inflows_sika, error="maturity_inflow_invalid"),
        outflows_sika=_amount(outflows_sika, error="maturity_outflow_invalid"),
    )


def forecast(
    *,
    treasury: sika_treasury_controls.TreasurySnapshot,
    maturity_buckets: Iterable[MaturityBucket],
    largest_outflow_share_percent: object = "0",
) -> ALMForecastSnapshot:
    buckets = tuple(maturity_buckets)
    if not buckets:
        raise ALMForecastError("maturity_buckets_required")

    concentration = _amount(
        largest_outflow_share_percent,
        error="largest_outflow_share_invalid",
    )
    if concentration > 100:
        raise ALMForecastError("largest_outflow_share_invalid")

    running = treasury.free_liquidity_sika
    minimum = running
    cumulative = Decimal("0.00")

    for item in buckets:
        cumulative += item.net_sika
        running += item.net_sika
        minimum = min(minimum, running)

    if minimum < 0:
        maturity_pressure = "SHORTFALL"
    elif minimum < treasury.operating_reserve_sika:
        maturity_pressure = "THIN"
    else:
        maturity_pressure = "COVERED"

    if running < treasury.free_liquidity_sika:
        reserve_trajectory = "DECLINING"
    elif running > treasury.free_liquidity_sika:
        reserve_trajectory = "IMPROVING"
    else:
        reserve_trajectory = "FLAT"

    if concentration >= Decimal(80):
        concentration_state = "HIGH"
    elif concentration >= Decimal(50):
        concentration_state = "WATCH"
    else:
        concentration_state = "DIVERSIFIED"

    review_required = any(
        (
            maturity_pressure != "COVERED",
            reserve_trajectory == "DECLINING",
            concentration_state in {"HIGH", "WATCH"},
        )
    )

    return ALMForecastSnapshot(
        starting_free_liquidity_sika=treasury.free_liquidity_sika,
        projected_free_liquidity_sika=running,
        minimum_projected_liquidity_sika=minimum,
        cumulative_net_flow_sika=cumulative,
        maturity_pressure_state=maturity_pressure,
        reserve_trajectory_state=reserve_trajectory,
        concentration_state=concentration_state,
        human_review_required=review_required,
        treasury_action_authorised=False,
        money_moved=False,
    )


def status() -> dict[str, object]:
    return {
        "system": "OAP ALM Forecasting Intelligence",
        "first_party": True,
        "mode": "deterministic_read_only",
        "maturity_bucket_forecasting": True,
        "liquidity_horizon_projection": True,
        "reserve_trajectory_intelligence": True,
        "concentration_intelligence": True,
        "hedge_execution": False,
        "treasury_action_authority": False,
        "money_movement": False,
        "human_authority_final": True,
    }
