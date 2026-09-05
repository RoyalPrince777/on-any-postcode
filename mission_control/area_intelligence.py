"""First-party OAP Atlas area intelligence.

This module is deliberately local and read-only. It gives OAP Atlas a useful
"what is in the area" surface without hidden tracking, external marketplace
authority, payment capture, dispatch, or fake live claims.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable

CATEGORIES = (
    "attractions",
    "food",
    "shops",
    "events",
    "sports",
    "music_culture",
    "parks_nature",
    "transport_movement",
    "stays_venues",
    "oap_direct",
    "youth_safe",
)

SEED_PLACES = (
    {
        "name": "Mitcham Town Centre",
        "area_key": "mitcham",
        "category": "shops",
        "type": "town_centre",
        "postcode": "CR4",
        "borough": "Merton",
        "county_region": "Greater London",
        "country": "United Kingdom",
        "continent": "Europe",
        "description": "Local shops, services and everyday movement starting point.",
        "source": "OAP founder seed",
        "youth_safe": True,
        "movement_ready": True,
        "direct_request_available": True,
        "oap_certified": False,
    },
    {
        "name": "Mitcham Common",
        "area_key": "mitcham",
        "category": "parks_nature",
        "type": "green_space",
        "postcode": "CR4",
        "borough": "Merton / Croydon / Sutton edge",
        "county_region": "Greater London",
        "country": "United Kingdom",
        "continent": "Europe",
        "description": "Green space, walking, wellbeing and nature signal.",
        "source": "OAP founder seed",
        "youth_safe": True,
        "movement_ready": True,
        "direct_request_available": False,
        "oap_certified": False,
    },
    {
        "name": "South London Culture Route",
        "area_key": "south london",
        "category": "music_culture",
        "type": "culture_route",
        "postcode": "SE / SW / CR",
        "borough": "South London",
        "county_region": "Greater London",
        "country": "United Kingdom",
        "continent": "Europe",
        "description": "Music, creator, food, sport and community culture route.",
        "source": "OAP founder seed",
        "youth_safe": True,
        "movement_ready": True,
        "direct_request_available": True,
        "oap_certified": False,
    },
    {
        "name": "Battersea Power Station Area",
        "area_key": "battersea",
        "category": "attractions",
        "type": "attraction_area",
        "postcode": "SW11",
        "borough": "Wandsworth",
        "county_region": "Greater London",
        "country": "United Kingdom",
        "continent": "Europe",
        "description": "Public attraction, shopping, food, riverside movement and venue area.",
        "source": "OAP founder seed",
        "youth_safe": True,
        "movement_ready": True,
        "direct_request_available": True,
        "oap_certified": False,
    },
    {
        "name": "Nunhead Local Spot",
        "area_key": "nunhead",
        "category": "food",
        "type": "local_area",
        "postcode": "SE15",
        "borough": "Southwark / Peckham edge",
        "county_region": "Greater London",
        "country": "United Kingdom",
        "continent": "Europe",
        "description": "Local food, shops, parks and South London culture.",
        "source": "OAP founder seed",
        "youth_safe": True,
        "movement_ready": True,
        "direct_request_available": True,
        "oap_certified": False,
    },
    {
        "name": "King's Cross Movement Hub",
        "area_key": "king's cross",
        "category": "transport_movement",
        "type": "transport_hub",
        "postcode": "N1C",
        "borough": "Camden / Islington edge",
        "county_region": "Greater London",
        "country": "United Kingdom",
        "continent": "Europe",
        "description": "Rail, underground, walking links, food, events and meeting point.",
        "source": "OAP founder seed",
        "youth_safe": True,
        "movement_ready": True,
        "direct_request_available": True,
        "oap_certified": False,
    },
    {
        "name": "London Bridge Riverside",
        "area_key": "london bridge",
        "category": "attractions",
        "type": "riverside_area",
        "postcode": "SE1",
        "borough": "Southwark",
        "county_region": "Greater London",
        "country": "United Kingdom",
        "continent": "Europe",
        "description": "River, food, culture, movement links and public attractions.",
        "source": "OAP founder seed",
        "youth_safe": True,
        "movement_ready": True,
        "direct_request_available": True,
        "oap_certified": False,
    },
    {
        "name": "Begoro / KORADASO Heritage Spot",
        "area_key": "begoro",
        "category": "music_culture",
        "type": "heritage_area",
        "postcode": "Begoro",
        "borough": "Fanteakwa area",
        "county_region": "Eastern Region",
        "country": "Ghana",
        "continent": "Africa",
        "description": "Akan, Akyem, Begoro and KORADASO heritage anchor for OAP expansion.",
        "source": "OAP founder seed",
        "youth_safe": True,
        "movement_ready": True,
        "direct_request_available": True,
        "oap_certified": False,
    },
    {
        "name": "KORADASO Royal Heritage Route",
        "area_key": "koradaso",
        "category": "attractions",
        "type": "heritage_route",
        "postcode": "KORADASO",
        "borough": "Akyem / Begoro area",
        "county_region": "Eastern Region",
        "country": "Ghana",
        "continent": "Africa",
        "description": "Founder heritage, culture, storytelling and future Direct experiences.",
        "source": "OAP founder seed",
        "youth_safe": True,
        "movement_ready": True,
        "direct_request_available": True,
        "oap_certified": False,
    },
)

KEY_ALIASES = {
    "cr4": "mitcham",
    "m town": "mitcham",
    "m-town": "mitcham",
    "south london": "south london",
    "sw11": "battersea",
    "se15": "nunhead",
    "n1c": "king's cross",
    "kings cross": "king's cross",
    "king cross": "king's cross",
    "se1": "london bridge",
    "koradaso": "koradaso",
    "begoro": "begoro",
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _normalise(value: object) -> str:
    return " ".join(str(value or "").strip().lower().split())


def _canonical_area(query: object) -> str:
    term = _normalise(query)
    if not term:
        return "mitcham"
    if term in KEY_ALIASES:
        return KEY_ALIASES[term]
    for key in KEY_ALIASES:
        if key in term:
            return KEY_ALIASES[key]
    return term


def _matches(area_key: str, place: dict[str, object]) -> bool:
    haystack = " ".join(
        str(place.get(field, ""))
        for field in (
            "area_key",
            "name",
            "postcode",
            "borough",
            "county_region",
            "country",
            "continent",
            "description",
        )
    ).lower()
    return area_key in haystack or str(place.get("area_key")) == area_key


def _category_counts(places: Iterable[dict[str, object]]) -> dict[str, int]:
    counts = {category: 0 for category in CATEGORIES}
    for place in places:
        category = str(place.get("category") or "")
        if category in counts:
            counts[category] += 1
        if place.get("direct_request_available"):
            counts["oap_direct"] += 1
        if place.get("youth_safe"):
            counts["youth_safe"] += 1
    return counts


def area_overview(query: object = None) -> dict[str, object]:
    """Return public-safe area intelligence for OAP Atlas."""

    area_key = _canonical_area(query)
    places = [dict(place) for place in SEED_PLACES if _matches(area_key, place)]
    if not places:
        places = [
            {
                "name": str(query or "Search area").strip() or "Search area",
                "area_key": area_key,
                "category": "oap_direct",
                "type": "area_placeholder",
                "postcode": "Not returned",
                "borough": "Not returned",
                "county_region": "Not returned",
                "country": "Not returned",
                "continent": "Not returned",
                "description": "Area search accepted. Add first-party listings or source proof to make this place green.",
                "source": "OAP search placeholder",
                "youth_safe": False,
                "movement_ready": False,
                "direct_request_available": True,
                "oap_certified": False,
            }
        ]

    primary = places[0]
    return {
        "component": "OAP Atlas Area Intelligence",
        "query": str(query or "Mitcham").strip() or "Mitcham",
        "area_key": area_key,
        "generated_at": _now(),
        "public": True,
        "private_state_exposed": False,
        "hidden_tracking": False,
        "live_claim": False,
        "live_ready": True,
        "proof_status": "seeded" if primary.get("source") == "OAP founder seed" else "building",
        "hierarchy": {
            "continent": primary.get("continent", "Not returned"),
            "country": primary.get("country", "Not returned"),
            "county_region": primary.get("county_region", "Not returned"),
            "borough_district": primary.get("borough", "Not returned"),
            "postcode": primary.get("postcode", "Not returned"),
            "spot": primary.get("name", "The Spot"),
        },
        "categories": _category_counts(places),
        "places": places,
        "source_health": {
            "source_order": ("OAP first-party", "Founder-approved", "public/open data", "OpenStreetMap future adapter"),
            "source": primary.get("source", "OAP search placeholder"),
            "source_timestamp": _now(),
            "external_provider_authority": False,
            "requires_live_source_to_claim_live": True,
        },
        "movement": {
            "ready": any(bool(place.get("movement_ready")) for place in places),
            "route_planning_enabled": True,
            "real_world_dispatch_enabled": False,
            "hidden_location_tracking_enabled": False,
            "consent_required_for_live_spot": True,
        },
        "direct": {
            "request_available": any(bool(place.get("direct_request_available")) for place in places),
            "confirmed_booking_enabled": False,
            "payment_capture_enabled": False,
            "supplier_receipt_required": True,
        },
        "green_gate": {
            "can_mark_area_green": all(
                bool(primary.get(field))
                for field in ("name", "category", "source", "country", "continent")
            ),
            "blocks_fake_live_claim": True,
            "blocks_hidden_tracking": True,
            "blocks_payment_capture": True,
            "blocks_dispatch": True,
        },
    }


def status() -> dict[str, object]:
    """Return private-safe status for War Room and proof runners."""

    sample = area_overview("Mitcham")
    return {
        "component": "Map Intelligence + Movement Area Engine",
        "public_surface": "/atlas",
        "api_surface": "/atlas/api/area",
        "seed_place_count": len(SEED_PLACES),
        "category_count": len(CATEGORIES),
        "sample_area": sample["area_key"],
        "live_ready": True,
        "live_claim": False,
        "hidden_tracking": False,
        "private_state_exposed": False,
        "movement_connected": True,
        "direct_connected": True,
        "dispatch_enabled": False,
        "payment_capture_enabled": False,
        "confirmed_booking_enabled": False,
        "next_gate": "Attach governed live/open-data source adapters and timestamped proof before claiming fully live area data.",
    }
