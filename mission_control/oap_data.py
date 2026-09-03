"""First-party OAP Data product contract.

OAP Data is the owned operational-data product for ON ANY POSTCODE. It gives
OAP Intelligence governed access to approved data without exposing raw private
records, credentials, or unrestricted database access.
"""
from __future__ import annotations

from typing import Any

PRODUCT_NAME = "OAP Data"
PRODUCT_OWNER = "ON ANY POSTCODE"
PRODUCT_MODE = "Private-first, governed, first-party"

PRODUCT_LAW: tuple[str, ...] = (
    "OAP Data is an OAP product, not a generic data label.",
    "OAP Data owns approved operational data contracts.",
    "OAP Intelligence may read only governed OAP Data projections.",
    "Private records are never exposed by the product-status surface.",
    "Human Authority remains final for destructive or high-impact data actions.",
    "External analytics, tracking and realtime-data providers are not required.",
)

DATA_DOMAINS: tuple[dict[str, str], ...] = (
    {
        "id": "identity",
        "name": "Identity Data",
        "purpose": "Canonical identity, role and permission records.",
        "boundary": "Private by default; access is identity and authority scoped.",
    },
    {
        "id": "link",
        "name": "Link Data",
        "purpose": "Link Up relationships, presence, signalling and bounded call session data.",
        "boundary": "Accepted-Link, Block and retention gates apply before access.",
    },
    {
        "id": "memory",
        "name": "Memory Data",
        "purpose": "HRM and JOOG MEMORY records used for governed continuity.",
        "boundary": "OAP Intelligence receives bounded context, not unrestricted history.",
    },
    {
        "id": "world",
        "name": "World Data",
        "purpose": "Postcode-to-Universe places, world state and local context.",
        "boundary": "Verified source and Human Authority rules apply to promoted state.",
    },
    {
        "id": "movement",
        "name": "Movement Data",
        "purpose": "Consent-scoped journeys, routing, availability and tracking records.",
        "boundary": "Location and tracking stay consent-bound and fail closed.",
    },
    {
        "id": "commerce",
        "name": "Commerce Data",
        "purpose": "OAP commerce, booking, fulfilment and payment-intent records.",
        "boundary": "No autonomous spending, settlement or financial execution.",
    },
    {
        "id": "media",
        "name": "Media Data",
        "purpose": "OAP TV, Music, Studio and approved private media records.",
        "boundary": "Content ownership, privacy and Guardian rules apply.",
    },
)

FIRST_PARTY_BOUNDARIES: dict[str, bool] = {
    "oap_product": True,
    "oap_owned_contracts": True,
    "external_analytics_required": False,
    "external_tracking_required": False,
    "external_realtime_data_provider_required": False,
    "public_raw_database_access": False,
    "unrestricted_intelligence_access": False,
    "human_authority_final": True,
}


def get_product_status() -> dict[str, Any]:
    """Return a coarse private product projection with no raw record values."""

    return {
        "product": PRODUCT_NAME,
        "owner": PRODUCT_OWNER,
        "mode": PRODUCT_MODE,
        "law": PRODUCT_LAW,
        "domains": DATA_DOMAINS,
        "first_party": FIRST_PARTY_BOUNDARIES,
        "consumer": "OAP Intelligence",
        "core": "OAP CORE",
        "raw_records_exposed": False,
        "destructive_actions_enabled": False,
    }
