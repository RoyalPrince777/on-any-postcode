"""SIKA Global first-party value and FX boundary.

This module does not create bank accounts, move money, issue cards, or fetch
third-party rates. It keeps one canonical SIKA denomination anchored at
1 SIKA = 1 GBP target value and accepts only explicit treasury rate snapshots.
"""
from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

SIKA_CODE = "SIKA"
ANCHOR_CODE = "GBP"
SIKA_TO_GBP = Decimal(1)
_CODE = re.compile(r"^[A-Z]{3}$")


class CurrencyError(ValueError):
    pass


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
    """Return a read-only local-currency quote.

    gbp_per_unit means the GBP value of one target-currency unit.
    Example: if 1 USD = 0.75 GBP, supply {"USD": "0.75"}.
    """
    amount = Decimal(str(amount_sika))
    if amount < 0:
        raise CurrencyError("amount_must_not_be_negative")
    code = normalize_currency(currency)

    if code == ANCHOR_CODE:
        rate = Decimal(1)
    else:
        try:
            rate = Decimal(str(gbp_per_unit[code]))
        except (KeyError, TypeError, ValueError) as exc:
            raise CurrencyError("treasury_rate_unavailable") from exc
        if rate <= 0:
            raise CurrencyError("treasury_rate_must_be_positive")

    gbp_value = amount * SIKA_TO_GBP
    local = (gbp_value / rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return Quote(
        sika=amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
        currency=code,
        local_amount=local,
        gbp_per_unit=rate,
        rate_source=rate_source,
        executable=False,
    )


def status() -> dict[str, object]:
    return {
        "system": "SIKA Global",
        "canonical_unit": SIKA_CODE,
        "anchor": {"currency": ANCHOR_CODE, "target": "1 SIKA = 1 GBP"},
        "global_currency_codes": (
            "any_valid_three_letter_iso_style_code_with_authorised_rate"
        ),
        "first_party_core": True,
        "client_calls_external_bank": False,
        "client_calls_external_fx_provider": False,
        "bank_accounts_enabled": False,
        "money_movement_enabled": False,
        "card_issuance_enabled": False,
        "cash_out_enabled": False,
        "regulated_execution_enabled": False,
        "human_approval_required": True,
    }
