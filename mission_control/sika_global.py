"""SIKA Global canonical value/FX boundary.

This module is deliberately non-executing. It defines the 1 SIKA = 1 GBP
founder target, validates treasury-provided quote inputs, and exposes the
release boundary for any later authorised payment/provider adapter.
"""
from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

from . import sika_financial_model

SIKA_CODE = "SIKA"
ANCHOR_CODE = "GBP"
SIKA_TO_GBP = Decimal(1)
_CODE = re.compile(r"^[A-Z]{3}$")


class CurrencyError(ValueError):
    """Raised when a quote input cannot be safely represented."""


@dataclass(frozen=True)
class Quote:
    sika: Decimal
    currency: str
    local_amount: Decimal
    gbp_per_unit: Decimal
    rate_source: str
    executable: bool = False

    def as_dict(self) -> dict[str, str | bool]:
        return {
            "sika": f"{self.sika:.2f}",
            "currency": self.currency,
            "local_amount": f"{self.local_amount:.2f}",
            "gbp_per_unit": str(self.gbp_per_unit),
            "rate_source": self.rate_source,
            "executable": self.executable,
        }


def _finite_decimal(value: Decimal | str | int, *, error: str) -> Decimal:
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise CurrencyError(error) from exc
    if not parsed.is_finite():
        raise CurrencyError(error)
    return parsed


def normalize_currency(code: str) -> str:
    value = str(code or "").strip().upper()
    if not _CODE.fullmatch(value):
        raise CurrencyError("currency_code_must_be_three_letters")
    return value


def quote_from_sika(
    amount_sika: Decimal | str | int,
    currency: str,
    *,
    gbp_per_unit: Mapping[str, Decimal | str | int],
    rate_source: str = "first_party_treasury_snapshot",
) -> Quote:
    """Return a read-only local-currency quote; never execute settlement."""
    amount = _finite_decimal(amount_sika, error="amount_must_be_finite")
    if amount < 0:
        raise CurrencyError("amount_must_not_be_negative")

    code = normalize_currency(currency)
    source = str(rate_source or "").strip()
    if not source:
        raise CurrencyError("rate_source_required")

    if code == ANCHOR_CODE:
        rate = Decimal(1)
    else:
        try:
            raw_rate = gbp_per_unit[code]
        except (KeyError, TypeError) as exc:
            raise CurrencyError("treasury_rate_unavailable") from exc
        rate = _finite_decimal(raw_rate, error="treasury_rate_must_be_finite")
        if rate <= 0:
            raise CurrencyError("treasury_rate_must_be_positive")

    gbp_value = amount * SIKA_TO_GBP
    local = (gbp_value / rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return Quote(
        sika=amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
        currency=code,
        local_amount=local,
        gbp_per_unit=rate,
        rate_source=source[:120],
        executable=False,
    )


def status() -> dict[str, object]:
    return {
        "system": "SIKA Global",
        "canonical_unit": SIKA_CODE,
        "anchor": {"currency": ANCHOR_CODE, "target": "1 SIKA = 1 GBP"},
        "first_party_core": True,
        "quote_execution_enabled": False,
        "regulated_execution_enabled": False,
        "customer_funds_enabled": False,
        "bank_accounts_enabled": False,
        "card_issuance_enabled": False,
        "cash_out_enabled": False,
        "provider_adapter_required": True,
        "provider_authority_evidence_required": True,
        "settlement_receipt_required": True,
        "human_authority_required": True,
        "financial_operating_model": sika_financial_model.status(),
    }
