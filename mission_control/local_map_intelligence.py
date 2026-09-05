"""UK-first On Any Place intelligence.

This layer keeps the public map focused on UK places, businesses, routes,
spots, travel requests and Live Pattern signals. It is public-safe: no hidden
user tracking, no payment capture, no automatic dispatch, and no copied
third-party branding. Live claims require timestamped source proof.
"""
from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
from typing import Iterable

PROGRAMS = {
    "company": "ON ANY POSTCODE",
    "places": "On Any Place",
    "routes": "On Any Route",
    "ride": "On Any Ride",
    "drop": "On Any Drop",
    "pattern": "Live Pattern",
    "direct": "OAP Direct",
    "private_checker": "War Room Simulation",
}

UK_CATEGORIES = (
    "all",
    "shops",
    "food",
    "local_businesses",
    "markets",
    "services",
    "barbers_hair",
    "pharmacies_health",
    "parks",
    "schools_youth",
    "sports",
    "music_culture",
    "venues",
    "events",
    "transport",
    "roads",
    "alleys",
    "traffic_signals",
    "parking",
    "toilets",
    "charging_fuel",
    "attractions",
    "ride_requests",
    "drop_requests",
)

FEATURE_UNLOCKS = {
    "uk_first": True,
    "on_any_place_surface": True,
    "on_any_route_preview": True,
    "on_any_ride_preview": True,
    "on_any_drop_preview": True,
    "live_pattern_surface": True,
    "spots_layer": True,
    "local_business_search": True,
    "shop_layer": True,
    "place_layer": True,
    "route_preview": True,
    "route_proof": True,
    "traffic_style_signals": True,
    "events_program_surface": True,
    "open_data_lookup_enabled": True,
    "movement_request_preview": True,
    "direct_request_entry": True,
    "live_source_timestamp_required": True,
    "payment_capture_enabled": False,
    "automatic_dispatch_enabled": False,
    "hidden_tracking_enabled": False,
    "third_party_branding_used": False,
}

LOCAL_POINTS = (
    {"name":"Mitcham Town Centre","area":"Mitcham","postcode":"CR4","borough":"Merton","category":"shops","kind":"high street","signal":"busy","description":"Everyday local shops, food, services and movement start point.","source":"OAP founder seed","live":False},
    {"name":"Mitcham Common","area":"Mitcham","postcode":"CR4","borough":"Merton edge","category":"parks","kind":"green space","signal":"clear","description":"Nature, walking, wellbeing and local route anchor.","source":"OAP founder seed","live":False},
    {"name":"Figges Marsh Edge","area":"Mitcham","postcode":"CR4","borough":"Merton","category":"parks","kind":"local open space","signal":"clear","description":"Neighbourhood park and walking route edge.","source":"OAP founder seed","live":False},
    {"name":"London Road Mitcham","area":"Mitcham","postcode":"CR4","borough":"Merton","category":"roads","kind":"main road","signal":"watch","description":"Main movement spine for shops, buses, routes and local access.","source":"OAP founder seed","live":False},
    {"name":"Mitcham Local Alley Links","area":"Mitcham","postcode":"CR4","borough":"Merton","category":"alleys","kind":"pedestrian link","signal":"review","description":"Small walking cuts and local links; needs source proof before live guidance.","source":"OAP founder seed","live":False},
    {"name":"Mitcham Business Row","area":"Mitcham","postcode":"CR4","borough":"Merton","category":"local_businesses","kind":"business cluster","signal":"steady","description":"Local business discovery lane for shops, services, food and owner claim flow later.","source":"OAP founder seed","live":False},
    {"name":"Mitcham Events Lane","area":"Mitcham","postcode":"CR4","borough":"Merton","category":"events","kind":"events program","signal":"watch","description":"What’s on, activity, venues and local event routes. Public live event claims require source proof.","source":"OAP founder seed","live":False},
    {"name":"On Any Ride Preview","area":"Mitcham","postcode":"CR4","borough":"Merton","category":"ride_requests","kind":"ride request preview","signal":"review","description":"Private-hire style request direction. Operator licence, driver assignment and payment remain locked.","source":"OAP founder seed","live":False},
    {"name":"On Any Drop Preview","area":"Mitcham","postcode":"CR4","borough":"Merton","category":"drop_requests","kind":"drop request preview","signal":"review","description":"Delivery and courier request direction. Assignment and payment remain locked.","source":"OAP founder seed","live":False},
    {"name":"Tooting / Mitcham Road Links","area":"South London","postcode":"SW17 / CR4","borough":"Wandsworth / Merton","category":"traffic_signals","kind":"route pressure","signal":"watch","description":"Live Pattern lane for route pressure, traffic-style signals and disruption proof.","source":"OAP founder seed","live":False},
    {"name":"Battersea Power Station Area","area":"Battersea","postcode":"SW11","borough":"Wandsworth","category":"attractions","kind":"destination area","signal":"busy","description":"Food, shops, attraction, riverside routes, venues and parking demand.","source":"OAP founder seed","live":False},
    {"name":"Nunhead Local Shops","area":"Nunhead","postcode":"SE15","borough":"Southwark","category":"local_businesses","kind":"local parade","signal":"steady","description":"Food, independent shops and South London neighbourhood services.","source":"OAP founder seed","live":False},
    {"name":"King’s Cross Movement Hub","area":"King's Cross","postcode":"N1C","borough":"Camden / Islington","category":"transport","kind":"station hub","signal":"busy","description":"Rail, underground, walking, food and meeting-point movement hub.","source":"OAP founder seed","live":False},
    {"name":"London Bridge Local Movement","area":"London Bridge","postcode":"SE1","borough":"Southwark","category":"transport","kind":"station and river route","signal":"busy","description":"Station, river, food, culture and high-footfall routes.","source":"OAP founder seed","live":False},
)

TRAFFIC_SIGNALS = (
    {"id":"clear","label":"Clear","meaning":"normal movement signal","colour":"green"},
    {"id":"steady","label":"Steady","meaning":"normal local flow","colour":"green"},
    {"id":"busy","label":"Busy","meaning":"high local demand or footfall","colour":"yellow"},
    {"id":"watch","label":"Watch","meaning":"needs live source proof before strong claim","colour":"yellow"},
    {"id":"review","label":"Review","meaning":"use with caution until route source proof exists","colour":"orange"},
    {"id":"blocked","label":"Blocked","meaning":"do not route until proof clears","colour":"red"},
)

ROUTE_PAIRS = {
    ("mitcham", "london bridge"): {"distance_km": 13.2, "drive_minutes": 42, "walk_minutes": 165, "cycle_minutes": 52, "transit_minutes": 48, "signal":"watch"},
    ("mitcham", "king's cross"): {"distance_km": 17.4, "drive_minutes": 55, "walk_minutes": 215, "cycle_minutes": 68, "transit_minutes": 58, "signal":"watch"},
    ("mitcham", "battersea"): {"distance_km": 9.5, "drive_minutes": 34, "walk_minutes": 118, "cycle_minutes": 38, "transit_minutes": 44, "signal":"steady"},
    ("nunhead", "london bridge"): {"distance_km": 5.2, "drive_minutes": 22, "walk_minutes": 63, "cycle_minutes": 21, "transit_minutes": 24, "signal":"busy"},
}

ALIASES = {
    "cr4": "mitcham",
    "m town": "mitcham",
    "m-town": "mitcham",
    "sw11": "battersea",
    "se15": "nunhead",
    "se1": "london bridge",
    "n1c": "king's cross",
    "kings cross": "king's cross",
    "king cross": "king's cross",
    "south london": "south london",
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _clean(value: object) -> str:
    return " ".join(str(value or "").strip().lower().split())


def canonical(value: object) -> str:
    term = _clean(value)
    if not term:
        return "mitcham"
    if term in ALIASES:
        return ALIASES[term]
    for key, mapped in ALIASES.items():
        if key in term:
            return mapped
    return term


def _matches(area_key: str, point: dict[str, object]) -> bool:
    haystack = " ".join(str(point.get(field, "")) for field in ("name", "area", "postcode", "borough", "category", "kind", "description")).lower()
    return area_key in haystack


def points_for(query: object = None, *, category: object = None) -> list[dict[str, object]]:
    generated_at = _now()
    area_key = canonical(query)
    category_key = _clean(category) or "all"
    points = [dict(point) for point in LOCAL_POINTS if _matches(area_key, point)]
    if not points and area_key == "south london":
        points = [dict(point) for point in LOCAL_POINTS if point.get("borough") in {"Merton", "Wandsworth", "Southwark"} or "South" in str(point.get("area"))]
    if category_key != "all":
        filtered = [point for point in points if _clean(point.get("category")) == category_key]
        points = filtered or points
    for point in points:
        point.update(
            country="United Kingdom",
            source_timestamp=generated_at,
            source_backed=True,
            live_source_backed=bool(point.get("live")),
            can_claim_live=bool(point.get("live")),
            public_safe=True,
            hidden_tracking=False,
            payment_capture=False,
            dispatch=False,
            direct_request_available=True,
            movement_ready=True,
        )
    return points


def _category_counts(points: Iterable[dict[str, object]]) -> dict[str, int]:
    counts = {category: 0 for category in UK_CATEGORIES if category != "all"}
    for point in points:
        category = str(point.get("category") or "")
        if category in counts:
            counts[category] += 1
    return counts


def route_proof(start: object = None, end: object = None, *, profile: object = "driving") -> dict[str, object]:
    origin = canonical(start)
    destination = canonical(end)
    generated_at = _now()
    profile_key = _clean(profile) or "driving"
    key = (origin, destination)
    reverse_key = (destination, origin)
    route = ROUTE_PAIRS.get(key) or ROUTE_PAIRS.get(reverse_key)
    if route is None:
        route = {"distance_km": None, "drive_minutes": None, "walk_minutes": None, "cycle_minutes": None, "transit_minutes": None, "signal":"review"}
        proof_state = "building"
    else:
        proof_state = "seed_route_proof"
    minutes_key = {
        "walking": "walk_minutes",
        "walk": "walk_minutes",
        "cycling": "cycle_minutes",
        "bike": "cycle_minutes",
        "transit": "transit_minutes",
        "train": "transit_minutes",
        "bus": "transit_minutes",
        "driving": "drive_minutes",
        "drive": "drive_minutes",
        "ride": "drive_minutes",
        "drop": "drive_minutes",
    }.get(profile_key, "drive_minutes")
    proof_id = sha256(f"{origin}|{destination}|{profile_key}|{generated_at[:16]}".encode()).hexdigest()[:16]
    return {
        "component": PROGRAMS["routes"],
        "proof_id": proof_id,
        "from": origin,
        "to": destination,
        "profile": profile_key,
        "distance_km": route["distance_km"],
        "eta_minutes": route[minutes_key],
        "traffic_style_signal": route["signal"],
        "source": "OAP UK seed route matrix",
        "source_timestamp": generated_at,
        "proof_state": proof_state,
        "live_traffic_claim": False,
        "live_route_geometry": False,
        "turn_by_turn_enabled": False,
        "can_request_movement": True,
        "payment_capture_enabled": False,
        "dispatch_enabled": False,
        "hidden_tracking_enabled": False,
        "next_gate": "Connect OSRM/local routing geometry and traffic/disruption source proof before live route guidance.",
    }


def request_preview(start: object = None, end: object = None, *, purpose: object = "on_any_route") -> dict[str, object]:
    route = route_proof(start, end)
    return {
        "component": "On Any Request Preview",
        "request_state": "preview_only",
        "purpose": str(purpose or "on_any_route")[:80],
        "route": route,
        "programs": PROGRAMS,
        "status_flow": ("requested", "reviewing", "route_ready", "supplier_needed", "blocked", "completed_after_proof"),
        "requires_contact_consent": True,
        "live_spot_consent_available": True,
        "payment_capture_enabled": False,
        "dispatch_enabled": False,
        "hidden_tracking_enabled": False,
    }


def local_map(query: object = None, *, category: object = None, start: object = None, end: object = None, profile: object = "driving") -> dict[str, object]:
    generated_at = _now()
    area_key = canonical(query or start or "Mitcham")
    points = points_for(area_key, category=category)
    route = route_proof(start or area_key, end or "London Bridge", profile=profile)
    return {
        "component": PROGRAMS["places"],
        "programs": PROGRAMS,
        "mode": "uk_first_places_routes_travel_spots",
        "query": str(query or area_key),
        "area_key": area_key,
        "country_scope": "United Kingdom",
        "generated_at": generated_at,
        "public": True,
        "brand_style": "OAP cockpit map",
        "third_party_branding_used": False,
        "public_noise_removed": True,
        "sections": {
            "maps": PROGRAMS["places"],
            "travel": PROGRAMS["direct"],
            "movement": PROGRAMS["routes"],
            "ride": PROGRAMS["ride"],
            "drop": PROGRAMS["drop"],
            "spots": "Spots",
            "events": PROGRAMS["pattern"],
        },
        "points": points,
        "point_count": len(points),
        "categories": _category_counts(points),
        "route": route,
        "traffic_signals": TRAFFIC_SIGNALS,
        "unlocks": FEATURE_UNLOCKS,
        "safety": {
            "payment_capture_enabled": False,
            "automatic_dispatch_enabled": False,
            "hidden_tracking_enabled": False,
            "live_traffic_claim": False,
            "live_claim_requires_timestamped_source": True,
            "public_private_boundary": "public_safe_fields_only",
        },
        "missing_before_green": (
            "real map tiles",
            "route line geometry",
            "turn-by-turn directions",
            "live traffic/disruption source",
            "UK-wide business ingestion with source proof",
            "events/open-now proof",
            "business owner listing tools",
            "reviews/photos/opening-hours source proof",
            "War Room proof runner pass",
        ),
    }


def status() -> dict[str, object]:
    sample = local_map("Mitcham")
    return {
        "component": "On Any Place Status",
        "programs": PROGRAMS,
        "country_scope": "United Kingdom",
        "public_surface": "/atlas",
        "preferred_public_surface": "/on-any-place",
        "compatibility_surfaces": ("/atlas", "/uk-map", "/business-map", "/traffic-map"),
        "place_api": "/atlas/api/local-map",
        "route_proof_api": "/movement/route-proof",
        "request_preview_api": "/movement/request-preview",
        "feature_unlocks": FEATURE_UNLOCKS,
        "point_count": len(LOCAL_POINTS),
        "category_count": len(UK_CATEGORIES),
        "traffic_signal_count": len(TRAFFIC_SIGNALS),
        "sample_area": sample["area_key"],
        "payment_capture_enabled": False,
        "automatic_dispatch_enabled": False,
        "hidden_tracking_enabled": False,
        "live_traffic_claim": False,
        "overall_green": False,
        "reason_not_green": "Surface and sections are live-ready, but real map tiles, full UK data, turn-by-turn, live traffic and event proof are not complete.",
    }
