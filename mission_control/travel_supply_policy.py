"""Canonical OAP Travel supply policy.

OAP Direct is the sovereign booking marketplace. External travel services may be
queried on demand as reference data when Human Authority chooses to fetch them,
but OAP does not persist that data as Partner Supply and does not grant external
services booking, payment, catalogue or platform authority.
"""
from __future__ import annotations

from typing import Any

TRAVEL_SUPPLY_POLICY_REVISION = "2026-09-04-v2"

NO_EXTERNAL_SUPPLIER_INDISPENSABLE = True
BOOKING_COM_REQUIRED = False
BOOKING_COM_PARTNER = False
DIRECT_SUPPLY_PREFERRED = True
EXTERNAL_LOOKUP_PERSISTED = False
PREFERRED_SOURCE_ORDER: tuple[str, ...] = ("oap_direct",)

SOURCE_LABELS = {
    "oap_direct": "🟢 OAP Direct",
    "certified_oap_supplier": "👑 Certified OAP Supplier",
    "external_lookup": "🔎 External Lookup",
}

PHASES: tuple[dict[str, str], ...] = (
    {"phase": "1", "strategy": "OAP Direct first-party marketplace"},
    {"phase": "2", "strategy": "Recruit Certified OAP suppliers"},
    {"phase": "3", "strategy": "Use external lookups only when useful"},
    {"phase": "4", "strategy": "Compare reference data without importing it"},
    {"phase": "5", "strategy": "Keep all external sources optional"},
)


def public_policy() -> dict[str, Any]:
    """Return non-secret policy metadata for public catalogue transparency."""

    return {
        "revision": TRAVEL_SUPPLY_POLICY_REVISION,
        "model": "oap_direct_with_optional_external_lookup",
        "no_external_supplier_indispensable": NO_EXTERNAL_SUPPLIER_INDISPENSABLE,
        "booking_com_required": BOOKING_COM_REQUIRED,
        "booking_com_partner": BOOKING_COM_PARTNER,
        "direct_supply_preferred": DIRECT_SUPPLY_PREFERRED,
        "external_lookup_persisted": EXTERNAL_LOOKUP_PERSISTED,
        "preferred_source_order": list(PREFERRED_SOURCE_ORDER),
        "source_labels": dict(SOURCE_LABELS),
        "external_provider_authority": False,
        "human_authority_final": True,
    }
