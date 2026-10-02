"""SIKA Treasury non-executing control layer.

Provides deterministic reserve, obligation and free-liquidity calculations.
It never moves funds, creates bank balances or authorises payment execution.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation


class TreasuryError(ValueError):
    """Raised when treasury inputs are invalid."""


def _amount(value: object, error: str) -> Decimal:
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise TreasuryError(error) from exc
    if not parsed.is_finite() or parsed < 0:
        raise TreasuryError(error)
    return parsed.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class TreasurySnapshot:
    available_sika: Decimal
    committed_sika: Decimal
    tax_reserved_sika: Decimal
    operating_reserve_sika: Decimal
    free_liquidity_sika: Decimal
    shortfall_sika: Decimal
    executable: bool = False

    def as_dict(self) -> dict[str, str | bool]:
        return {
            "available_sika": f"{self.available_sika:.2f}",
            "committed_sika": f"{self.committed_sika:.2f}",
            "tax_reserved_sika": f"{self.tax_reserved_sika:.2f}",
            "operating_reserve_sika": f"{self.operating_reserve_sika:.2f}",
            "free_liquidity_sika": f"{self.free_liquidity_sika:.2f}",
            "shortfall_sika": f"{self.shortfall_sika:.2f}",
            "executable": self.executable,
        }


def snapshot(
    *,
    available_sika: object,
    committed_sika: object = "0",
    tax_reserved_sika: object = "0",
    operating_reserve_sika: object = "0",
) -> TreasurySnapshot:
    available = _amount(available_sika, "available_sika_invalid")
    committed = _amount(committed_sika, "committed_sika_invalid")
    tax_reserved = _amount(tax_reserved_sika, "tax_reserved_sika_invalid")
    operating_reserve = _amount(
        operating_reserve_sika,
        "operating_reserve_sika_invalid",
    )

    obligations = committed + tax_reserved + operating_reserve
    free = max(available - obligations, Decimal(0))
    shortfall = max(obligations - available, Decimal(0))

    return TreasurySnapshot(
        available_sika=available,
        committed_sika=committed,
        tax_reserved_sika=tax_reserved,
        operating_reserve_sika=operating_reserve,
        free_liquidity_sika=free,
        shortfall_sika=shortfall,
        executable=False,
    )


def release_gate(state: TreasurySnapshot) -> dict[str, object]:
    healthy = state.shortfall_sika == 0
    return {
        "liquidity_healthy": healthy,
        "free_liquidity_sika": f"{state.free_liquidity_sika:.2f}",
        "shortfall_sika": f"{state.shortfall_sika:.2f}",
        "may_enter_payment_review": healthy,
        "payment_execution_authorised": False,
        "money_moved": False,
        "provider_adapter_required": True,
        "settlement_receipt_required": True,
        "human_authority_required": True,
    }


def status() -> dict[str, object]:
    return {
        "system": "SIKA Treasury Controls",
        "calculates_liquidity": True,
        "tracks_obligations": True,
        "tracks_tax_reserve": True,
        "tracks_operating_reserve": True,
        "payment_execution_enabled": False,
        "money_movement_enabled": False,
        "provider_adapter_required": True,
        "settlement_receipt_required": True,
        "human_authority_required": True,
    }
