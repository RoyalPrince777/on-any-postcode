"""SIKA display-only Manifest quotation. No money movement, ledger issuance or payment rights.

Pure integer-pence arithmetic; do not use this module as a live checkout.
"""
from __future__ import annotations

from dataclasses import dataclass

MAX_PENCE = 10_000_000_00  # £10 million display bound
AREA_TYPES = frozenset({"postcode", "borough", "county_region", "country", "global"})


@dataclass(frozen=True)
class ManifestQuote:
    purchase_pence: int
    optional_manifest_pence: int
    area_type: str | None
    area_allocation_pence: int
    remaining_manifest_pence: int
    total_pence: int
    status: str = "QUOTE_ONLY_NO_PAYMENT"


def quote_manifest(
    purchase_pence: int, optional_manifest_pence: int = 0,
    area_type: str | None = None,
) -> ManifestQuote:
    """Quote 7% of optional Manifest More only, rounded half-up to pennies.

    A geographic choice names an *area type*, not a verified payee.
    Actual recipient validation, fee allocation and payment are out of scope.
    """
    for value in (purchase_pence, optional_manifest_pence):
        if type(value) is not int or not (0 <= value <= MAX_PENCE):
            raise ValueError("amount_must_be_nonnegative_integer_pence")
    if purchase_pence + optional_manifest_pence > MAX_PENCE:
        raise ValueError("amount_exceeds_quote_limit")
    if optional_manifest_pence and area_type not in AREA_TYPES:
        raise ValueError("eligible_area_type_required")
    if not optional_manifest_pence and area_type is not None and area_type not in AREA_TYPES:
        raise ValueError("invalid_area_type")
    allocation = (optional_manifest_pence * 7 + 50) // 100
    return ManifestQuote(
        purchase_pence=purchase_pence,
        optional_manifest_pence=optional_manifest_pence,
        area_type=area_type,
        area_allocation_pence=allocation,
        remaining_manifest_pence=optional_manifest_pence-allocation,
        total_pence=purchase_pence+optional_manifest_pence,
    )
