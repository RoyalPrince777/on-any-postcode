"""Barber price quotes via real OAP Direct inventory and non-executing SIKA.

Barber sets the price and real appointment slot through certified supply.
This bridge neither creates a booking nor charges the customer: SIKA gateway,
payment authority, settlement and supplier confirmation remain independent.
"""
from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from . import barber_supply_extension, sika_global, travel_marketplace


def quote_for_slot(payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise TypeError("json_object_required")
    if not barber_supply_extension.status()["schema_ready"]:
        raise RuntimeError("barber_supply_schema_not_ready")
    qty = payload.get("quantity", 1)
    if isinstance(qty, bool) or not isinstance(qty, int) or qty != 1:
        raise ValueError("one_appointment_per_booking_required")

    # This method fetches current certified supply from the first-party DB.
    # Never accept a price, merchant identity or confirmation from the client.
    quote = travel_marketplace.quote_direct({
        "listing_id": payload.get("listing_id"),
        "starts_at": payload.get("starts_at"),
        "ends_at": payload.get("ends_at"),
        "quantity": 1,
    })
    if (
        quote.get("source") != "oap_direct"
        or quote.get("category") != "barber"
        or quote.get("observed_not_inferred") is not True
        or quote.get("requested_quantity") != 1
        or quote.get("provider_authority") is not False
    ):
        raise ValueError("certified_barber_slot_required")
    starts_at = datetime.fromisoformat(str(quote.get("starts_at") or ""))
    ends_at = datetime.fromisoformat(str(quote.get("ends_at") or ""))
    if (
        starts_at.tzinfo is None
        or ends_at.tzinfo is None
        or starts_at <= datetime.now(UTC)
        or ends_at <= starts_at
    ):
        raise ValueError("future_barber_appointment_required")
    if quote.get("currency") != "GBP":
        raise ValueError("barber_gbp_anchor_required")
    minor = quote.get("total_price_minor")
    if (
        isinstance(minor, bool) or not isinstance(minor, int)
        or not 1 <= minor <= 100000000
        or quote.get("unit_price_minor") != minor
    ):
        raise ValueError("certified_barber_price_required")
    amount = Decimal(minor) / Decimal(100)
    priced = sika_global.quote_from_sika(
        amount, "GBP", gbp_per_unit={}, rate_source="OAP Direct certified supplier quote"
    ).as_dict()
    return {
        "component": "OAP Barber SIKA Quote",
        "source": "oap_direct_certified_barber_slot",
        "listing_id": quote["listing_id"],
        "slot_id": quote["slot_id"],
        "supplier_id": quote["supplier_id"],
        "supplier_name": quote["supplier_name"],
        "service": quote["title"],
        "starts_at": quote["starts_at"],
        "ends_at": quote["ends_at"],
        "observed_at": quote["observed_at"],
        "appointment_quantity": 1,
        "sika_amount": priced["sika"],
        "gbp_amount": priced["local_amount"],
        "anchor": "1 SIKA = 1 GBP",
        "pricing_executable": False,
        "booking_state": "QUOTE_ONLY",
        "supplier_confirmed": False,
        "payment_request_created": False,
        "payment_authorised": False,
        "settlement_proven": False,
        "money_moved": False,
        "founder_final": True,
    }
