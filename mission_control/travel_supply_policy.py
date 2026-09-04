"""Canonical OAP Travel supply policy.

Only directly onboarded Certified OAP Suppliers enter the OAP Travel catalogue.
External travel information may still be fetched on demand for research or
comparison, but it is not treated as Partner Supply, imported catalogue inventory
or booking authority.
"""
from __future__ import annotations

from typing import Any

TRAVEL_SUPPLY_POLICY_REVISION = "2026-09-04-v2"
DIRECT_SUPPLY_PREFERRED = True
EXTERNAL_DATA_FETCH_ALLOWED = True
EXTERNAL_CATALOGUE_IMPORT_ALLOWED = False
PREFERRED_SOURCE_ORDER: tuple[str, ...] = ("oap_direct",)

SOURCE_LABELS = {
    "oap_direct": "🟢 OAP Direct",
    "certified_oap_supplier": "👑 Certified OAP Supplier",
}

PHASES: tuple[dict[str, str], ...] = (
    {"phase": "1", "strategy": "Build OAP Direct supplier inventory"},
    {"phase": "2", "strategy": "Recruit and certify real OAP suppliers"},
    {"phase": "3", "strategy": "Expand availability, pricing and listing media"},
    {"phase": "4", "strategy": "Use external data only as on-demand research context"},
    {"phase": "5", "strategy": "Keep OAP Travel independent of external marketplaces"},
)


def public_policy() -> dict[str, Any]:
    return {
        "revision": TRAVEL_SUPPLY_POLICY_REVISION,
        "model": "oap_direct_only_catalogue",
        "direct_supply_preferred": DIRECT_SUPPLY_PREFERRED,
        "external_data_fetch_allowed": EXTERNAL_DATA_FETCH_ALLOWED,
        "external_catalogue_import_allowed": EXTERNAL_CATALOGUE_IMPORT_ALLOWED,
        "preferred_source_order": list(PREFERRED_SOURCE_ORDER),
        "source_labels": dict(SOURCE_LABELS),
        "external_provider_authority": False,
        "human_authority_final": True,
    }
