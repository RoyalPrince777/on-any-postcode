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

SOURCE_ADAPTERS = (
    {
        "id": "oap_first_party",
        "name": "OAP first-party places",
        "state": "ready",
        "signal": "green",
        "authority": "OAP controlled",
        "can_mark_live": True,
    },
    {
        "id": "founder_approved",
        "name": "Founder-approved local places",
        "state": "ready",
        "signal": "green",
        "authority": "Founder controlled",
        "can_mark_live": True,
    },
    {
        "id": "local_open_data",
        "name": "Local council / tourism open data",
        "state": "adapter_ready",
        "signal": "yellow",
        "authority": "external public source, no marketplace authority",
        "can_mark_live": False,
    },
    {
        "id": "openstreetmap",
        "name": "OpenStreetMap places",
        "state": "adapter_ready",
        "signal": "yellow",
        "authority": "open map data, source proof required",
        "can_mark_live": False,
    },
    {
        "id": "weather_safety",
        "name": "Weather / safety / travel signals",
        "state": "source_bound",
        "signal": "yellow",
        "authority": "source timestamp required",
        "can_mark_live": False,
    },
)

OPEN_DATA_ADAPTER_CONTRACT = {
    "component": "OAP Atlas Open Data Adapter Contract",
    "mode": "governed_source_fetcher",
    "public": True,
    "private_state_exposed": False,
    "hidden_tracking": False,
    "external_marketplace_authority": False,
    "payment_capture_enabled": False,
    "dispatch_enabled": False,
    "confirmed_booking_enabled": False,
    "allowed_sources": (
        "OAP first-party places",
        "Founder-approved local places",
        "local council / tourism open data",
        "OpenStreetMap / Overpass-style public places",
        "weather / safety / travel signals with timestamp",
    ),
    "fetch_rules": {
        "timeout_seconds": 8,
        "max_results_per_source": 25,
        "requires_source_name": True,
        "requires_source_timestamp": True,
        "requires_attribution": True,
        "requires_category_mapping": True,
        "requires_public_safe_fields_only": True,
        "no_user_background_tracking": True,
        "no_precise_user_location_without_consent": True,
    },
    "green_gate": {
        "seeded_places_can_be_area_green": True,
        "live_claim_requires_live_fetch_success": True,
        "live_claim_requires_timestamp": True,
        "live_claim_requires_attribution": True,
        "blocks_fake_live_claim": True,
        "blocks_hidden_tracking": True,
        "blocks_payment_capture": True,
        "blocks_dispatch": True,
    },
}

SEED_PLACES = (
    {"name":"Mitcham Town Centre","area_key":"mitcham","category":"shops","type":"town_centre","postcode":"CR4","borough":"Merton","county_region":"Greater London","country":"United Kingdom","continent":"Europe","description":"Local shops, services and everyday movement starting point.","source":"OAP founder seed","source_tier":"founder_approved","youth_safe":True,"movement_ready":True,"direct_request_available":True,"oap_certified":False},
    {"name":"Mitcham Common","area_key":"mitcham","category":"parks_nature","type":"green_space","postcode":"CR4","borough":"Merton / Croydon / Sutton edge","county_region":"Greater London","country":"United Kingdom","continent":"Europe","description":"Green space, walking, wellbeing and nature signal.","source":"OAP founder seed","source_tier":"founder_approved","youth_safe":True,"movement_ready":True,"direct_request_available":False,"oap_certified":False},
    {"name":"South London Culture Route","area_key":"south london","category":"music_culture","type":"culture_route","postcode":"SE / SW / CR","borough":"South London","county_region":"Greater London","country":"United Kingdom","continent":"Europe","description":"Music, creator, food, sport and community culture route.","source":"OAP founder seed","source_tier":"founder_approved","youth_safe":True,"movement_ready":True,"direct_request_available":True,"oap_certified":False},
    {"name":"Battersea Power Station Area","area_key":"battersea","category":"attractions","type":"attraction_area","postcode":"SW11","borough":"Wandsworth","county_region":"Greater London","country":"United Kingdom","continent":"Europe","description":"Public attraction, shopping, food, riverside movement and venue area.","source":"OAP founder seed","source_tier":"founder_approved","youth_safe":True,"movement_ready":True,"direct_request_available":True,"oap_certified":False},
    {"name":"Nunhead Local Spot","area_key":"nunhead","category":"food","type":"local_area","postcode":"SE15","borough":"Southwark / Peckham edge","county_region":"Greater London","country":"United Kingdom","continent":"Europe","description":"Local food, shops, parks and South London culture.","source":"OAP founder seed","source_tier":"founder_approved","youth_safe":True,"movement_ready":True,"direct_request_available":True,"oap_certified":False},
    {"name":"King's Cross Movement Hub","area_key":"king's cross","category":"transport_movement","type":"transport_hub","postcode":"N1C","borough":"Camden / Islington edge","county_region":"Greater London","country":"United Kingdom","continent":"Europe","description":"Rail, underground, walking links, food, events and meeting point.","source":"OAP founder seed","source_tier":"founder_approved","youth_safe":True,"movement_ready":True,"direct_request_available":True,"oap_certified":False},
    {"name":"London Bridge Riverside","area_key":"london bridge","category":"attractions","type":"riverside_area","postcode":"SE1","borough":"Southwark","county_region":"Greater London","country":"United Kingdom","continent":"Europe","description":"River, food, culture, movement links and public attractions.","source":"OAP founder seed","source_tier":"founder_approved","youth_safe":True,"movement_ready":True,"direct_request_available":True,"oap_certified":False},
    {"name":"Begoro / KORADASO Heritage Spot","area_key":"begoro","category":"music_culture","type":"heritage_area","postcode":"Begoro","borough":"Fanteakwa area","county_region":"Eastern Region","country":"Ghana","continent":"Africa","description":"Akan, Akyem, Begoro and KORADASO heritage anchor for OAP expansion.","source":"OAP founder seed","source_tier":"founder_approved","youth_safe":True,"movement_ready":True,"direct_request_available":True,"oap_certified":False},
    {"name":"KORADASO Royal Heritage Route","area_key":"koradaso","category":"attractions","type":"heritage_route","postcode":"KORADASO","borough":"Akyem / Begoro area","county_region":"Eastern Region","country":"Ghana","continent":"Africa","description":"Founder heritage, culture, storytelling and future Direct experiences.","source":"OAP founder seed","source_tier":"founder_approved","youth_safe":True,"movement_ready":True,"direct_request_available":True,"oap_certified":False},
)

KEY_ALIASES = {
    "cr4": "mitcham", "m town": "mitcham", "m-town": "mitcham",
    "south london": "south london", "sw11": "battersea", "se15": "nunhead",
    "n1c": "king's cross", "kings cross": "king's cross", "king cross": "king's cross",
    "se1": "london bridge", "koradaso": "koradaso", "begoro": "begoro",
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
        for field in ("area_key", "name", "postcode", "borough", "county_region", "country", "continent", "description")
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


def _adapter_state(source_tier: object) -> dict[str, object]:
    tier = str(source_tier or "founder_approved")
    return next((dict(item) for item in SOURCE_ADAPTERS if item["id"] == tier), dict(SOURCE_ADAPTERS[0]))


def _proofed_place(place: dict[str, object], generated_at: str) -> dict[str, object]:
    enriched = dict(place)
    adapter = _adapter_state(enriched.get("source_tier"))
    source_present = bool(enriched.get("source"))
    hierarchy_present = all(bool(enriched.get(key)) for key in ("country", "continent", "postcode"))
    source_backed = adapter["id"] in {"oap_first_party", "founder_approved"} and source_present
    enriched.update(
        source_adapter=adapter["id"],
        source_adapter_state=adapter["state"],
        source_timestamp=generated_at,
        source_backed=source_backed,
        live_source_backed=False,
        freshness="current_session_seed" if source_backed else "awaiting_source",
        proof_lane="green" if source_backed and hierarchy_present else "yellow",
        confidence="medium" if source_backed else "low",
        can_show_publicly=True,
        can_claim_live=False,
        no_hidden_tracking=True,
        external_provider_authority=False,
    )
    return enriched


def open_data_adapter_status(query: object = None) -> dict[str, object]:
    """Return the governed open-data adapter contract without fetching externally."""

    generated_at = _now()
    area_key = _canonical_area(query)
    return {
        **OPEN_DATA_ADAPTER_CONTRACT,
        "area_key": area_key,
        "generated_at": generated_at,
        "fetch_enabled": False,
        "last_fetch_status": "not_run_in_request",
        "last_fetch_timestamp": None,
        "results_imported": 0,
        "source_backed_live_places": 0,
        "can_claim_live_now": False,
        "next_step": "Enable a controlled server-side fetcher with attribution, timeout and HRM receipt after Founder approval.",
    }


def area_overview(query: object = None) -> dict[str, object]:
    """Return public-safe area intelligence for OAP Atlas."""

    generated_at = _now()
    area_key = _canonical_area(query)
    places = [dict(place) for place in SEED_PLACES if _matches(area_key, place)]
    if not places:
        places = [{
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
            "source_tier": "local_open_data",
            "youth_safe": False,
            "movement_ready": False,
            "direct_request_available": True,
            "oap_certified": False,
        }]

    places = [_proofed_place(place, generated_at) for place in places]
    primary = places[0]
    source_backed_count = sum(1 for place in places if place.get("source_backed"))
    live_source_count = sum(1 for place in places if place.get("live_source_backed"))
    return {
        "component": "OAP Atlas Area Intelligence",
        "query": str(query or "Mitcham").strip() or "Mitcham",
        "area_key": area_key,
        "generated_at": generated_at,
        "public": True,
        "private_state_exposed": False,
        "hidden_tracking": False,
        "live_claim": live_source_count > 0,
        "live_ready": True,
        "proof_status": "source_backed_seed" if source_backed_count else "building",
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
            "adapters": SOURCE_ADAPTERS,
            "open_data_adapter": open_data_adapter_status(query),
            "source_order": ("OAP first-party", "Founder-approved", "public/open data", "OpenStreetMap future adapter"),
            "source": primary.get("source", "OAP search placeholder"),
            "source_timestamp": generated_at,
            "source_backed_count": source_backed_count,
            "live_source_count": live_source_count,
            "seeded_count": len(places),
            "external_provider_authority": False,
            "requires_live_source_to_claim_live": True,
        },
        "movement": {
            "ready": any(bool(place.get("movement_ready")) for place in places),
            "route_planning_enabled": True,
            "area_to_movement_connected": True,
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
            "can_mark_area_green": source_backed_count > 0 and all(bool(primary.get(field)) for field in ("name", "category", "source", "country", "continent")),
            "can_mark_live_green": live_source_count > 0,
            "blocks_fake_live_claim": True,
            "blocks_hidden_tracking": True,
            "blocks_payment_capture": True,
            "blocks_dispatch": True,
        },
    }


def status() -> dict[str, object]:
    """Return private-safe status for War Room and proof runners."""

    sample = area_overview("Mitcham")
    adapter = open_data_adapter_status("Mitcham")
    return {
        "component": "Map Intelligence + Movement Area Engine",
        "public_surface": "/atlas",
        "api_surface": "/atlas/api/area",
        "seed_place_count": len(SEED_PLACES),
        "category_count": len(CATEGORIES),
        "source_adapter_count": len(SOURCE_ADAPTERS),
        "source_adapters": SOURCE_ADAPTERS,
        "open_data_adapter": adapter,
        "sample_area": sample["area_key"],
        "source_backed_count": sample["source_health"]["source_backed_count"],
        "live_source_count": sample["source_health"]["live_source_count"],
        "live_ready": True,
        "live_claim": False,
        "hidden_tracking": False,
        "private_state_exposed": False,
        "movement_connected": True,
        "direct_connected": True,
        "dispatch_enabled": False,
        "payment_capture_enabled": False,
        "confirmed_booking_enabled": False,
        "next_gate": "Enable governed OpenStreetMap/local-open-data fetchers with timestamped source proof, attribution, HRM receipt and Founder approval before claiming fully live area data.",
    }
