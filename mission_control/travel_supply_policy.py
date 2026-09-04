"""Canonical OAP Travel supply policy.

OAP owns the travel catalogue, comparison and booking journey. Direct suppliers
are preferred. External providers are replaceable supply sources and may never
become an authority or indispensable dependency.
"""
from __future__ import annotations

from typing import Any

TRAVEL_SUPPLY_POLICY_REVISION = "2026-09-04-v1"

NO_EXTERNAL_SUPPLIER_INDISPENSABLE = True
BOOKING_COM_REQUIRED = False
DIRECT_SUPPLY_PREFERRED = True
PREFERRED_SOURCE_ORDER: tuple[str, ...] = ("oap_direct", "partner_supply")

SOURCE_LABELS = {
    "oap_direct": "🟢 OAP Direct",
    "certified_oap_supplier": "👑 Certified OAP Supplier",
    "partner_supply": "🔗 Partner Supply",
}

PHASES: tuple[dict[str, str], ...] = (
    {"phase": "1", "strategy": "Booking.com + OAP Direct"},
    {"phase": "2", "strategy": "Recruit OAP Direct suppliers aggressively"},
    {"phase": "3", "strategy": "Prefer OAP Direct where comparable"},
    {"phase": "4", "strategy": "Add multiple replaceable partner sources"},
    {"phase": "5", "strategy": "Booking.com becomes optional rather than critical"},
)


def public_policy() -> dict[str, Any]:
    """Return non-secret policy metadata for public catalogue transparency."""

    return {
        "revision": TRAVEL_SUPPLY_POLICY_REVISION,
        "model": "hybrid_oap_travel",
        "no_external_supplier_indispensable": NO_EXTERNAL_SUPPLIER_INDISPENSABLE,
        "booking_com_required": BOOKING_COM_REQUIRED,
        "direct_supply_preferred": DIRECT_SUPPLY_PREFERRED,
        "preferred_source_order": list(PREFERRED_SOURCE_ORDER),
        "source_labels": dict(SOURCE_LABELS),
        "external_provider_authority": False,
        "human_authority_final": True,
    }
