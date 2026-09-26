"""UK-first On Any Place / Map Intelligence.

This layer keeps the public map focused on UK places, businesses, routes,
spots, travel requests and Live Pattern signals. Travel and Movement sit inside
Map Intelligence so the user journey is place-first, route-aware and proof-gated.
It is public-safe: no hidden user tracking, no payment capture, no automatic
dispatch, and no copied third-party branding. Live claims require timestamped
source proof.
"""
from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
from typing import Iterable

PROGRAMS = {
    "company": "ON ANY POSTCODE",
    "map_intelligence": "Map Intelligence",
    "places": "On Any Place",
    "routes": "On Any Route",
    "travel": "Travel",
    "movement": "Movement",
    "ride": "On Any Ride",
    "drop": "On Any Drop",
    "pattern": "Live Pattern",
    "direct": "OAP Direct",
    "private_checker": "War Room Simulation",
}

MAP_INTELLIGENCE_STRUCTURE = {
    "root": "On Any Place",
    "private_brain": "Map Intelligence",
    "public_rule": "Places first. Travel and Movement sit inside the map, not outside it.",
    "layers": {
        "places": "Shops, food, businesses, parks, venues, attractions and Spots.",
        "travel": "OAP Direct requests, venues, stays, attractions and travel supply proof.",
        "movement": "On Any Route, walking, cycling, driving, transit-style preview and route proof.",
        "ride": "On Any Ride request preview; licence, payment and dispatch locked.",
        "drop": "On Any Drop request preview; courier assignment, payment and dispatch locked.",
        "live_pattern": "Traffic-style, event, crowd and open-now signals; true live claims require timestamps.",
    },
    "green_rule": "Map Intelligence cannot go overall green until map tiles, route geometry, source-backed UK data, events/open-now proof and War Room proof-runner pass.",
}

MAP_SEEING_LAYERS = {
    "principle": "Map Intelligence sees the world through layered proof, not one magic provider.",
    "google_waze_tesla_lesson": {
        "google_style": "imagery, Street View-style observations, business/place data, user reports, authority data and AI change detection",
        "waze_style": "driver movement, crowd reports, hazards, closures and partner/authority feeds",
        "tesla_style": "onboard map, vehicle GPS, online routing, live traffic visualisation and vehicle/charger state",
        "oap_style": "open map data, first-party local proof, Founder-approved seeds, public open data, consent-only Live Spot and HRM receipts",
    },
    "oap_layers": {
        "base_map": "OpenStreetMap/open map geometry, local tiles later, offline-friendly where possible.",
        "imagery_reference": "Optional aerial/satellite/photo references only when licensed/source-backed; no copied third-party branding.",
        "place_data": "Shops, food, businesses, venues, parks, attractions, stations and Spots.",
        "movement_data": "Routes, distance, ETA, route pressure and source-backed geometry.",
        "travel_data": "Direct requests, stays, venues, attractions and supplier proof.",
        "live_pattern": "Traffic-style, events, crowd pressure, disruption and open-now signals with timestamps.",
        "proof_layer": "Source name, source timestamp, freshness, confidence, stale warning and proof_id.",
        "consent_layer": "Live Spot/location features require permission, expiry, stop/delete and no silent tracking.",
        "green_gate": "No live claim, full-green claim, payment, dispatch or confirmation without proof.",
    },
    "hard_locks": {
        "payment_capture_enabled": False,
        "automatic_dispatch_enabled": False,
        "hidden_tracking_enabled": False,
        "fake_live_claim_enabled": False,
        "third_party_branding_used": False,
    },
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
    "travel_requests",
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
    "map_intelligence_root": True,
    "map_seeing_layers": True,
    "base_map_layer_defined": True,
    "place_data_layer_defined": True,
    "movement_data_layer_defined": True,
    "travel_data_layer_defined": True,
    "live_pattern_layer_defined": True,
    "proof_layer_defined": True,
    "consent_layer_defined": True,
    "green_gate_layer_defined": True,
    "travel_inside_map_intelligence": True,
    "movement_inside_map_intelligence": True,
    "on_any_place_surface": True,
    "on_any_route_preview": True,
    "on_any_ride_preview": True,
    "on_any_drop_preview": True,
    "live_pattern_surface": True,
    "spots_layer": True,
    "travel_request_preview": True,
    "local_business_search": True,
    "shop_layer": True,
    "place_layer": True,
    "route_preview": True,
    "route_proof": True,
    "road_vector_tiles": True,
    "route_geometry": True,
    "turn_by_turn_navigation": True,
    "voice_turn_guidance": True,
    "off_route_reroute": True,
    "traffic_style_signals": True,
    "authority_disruption_adapter": True,
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
    {"name":"Mitcham Travel Direct Lane","area":"Mitcham","postcode":"CR4","borough":"Merton","category":"travel_requests","kind":"travel inside map","signal":"review","description":"Travel requests sit inside Map Intelligence through OAP Direct. Supplier proof, confirmation and payment stay locked.","source":"OAP founder seed","live":False},
    {"name":"Mitcham Movement Lane","area":"Mitcham","postcode":"CR4","borough":"Merton","category":"transport","kind":"movement inside map","signal":"watch","description":"Movement sits inside Map Intelligence as route proof, consent-only requests and On Any Route preview.","source":"OAP founder seed","live":False},
    {"name":"Mitcham Events Lane","area":"Mitcham","postcode":"CR4","borough":"Merton","category":"events","kind":"events program","signal":"watch","description":"What’s on, activity, venues and local event routes. Public live event claims require source proof.","source":"OAP founder seed","live":False},
    {"name":"On Any Ride Preview","area":"Mitcham","postcode":"CR4","borough":"Merton","category":"ride_requests","kind":"ride request preview","signal":"review","description":"Private-hire style request direction inside Map Intelligence. Operator licence, driver assignment and payment remain locked.","source":"OAP founder seed","live":False},
    {"name":"On Any Drop Preview","area":"Mitcham","postcode":"CR4","borough":"Merton","category":"drop_requests","kind":"drop request preview","signal":"review","description":"Delivery and courier request direction inside Map Intelligence. Assignment and payment remain locked.","source":"OAP founder seed","live":False},
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
            map_intelligence_layer=True,
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
        "parent": PROGRAMS["map_intelligence"],
        "inside": PROGRAMS["places"],
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
        "seeing_layers": ("movement_data", "proof_layer", "green_gate"),
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
        "parent": PROGRAMS["map_intelligence"],
        "inside": PROGRAMS["places"],
        "seeing_layers": ("travel_data", "movement_data", "consent_layer", "proof_layer", "green_gate"),
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


def readiness_state() -> dict[str, object]:
    """Reconcile the public On Any Place truth board with the active runtime stack."""
    from . import (
        atlas_live_sources,
        certification,
        listing_media,
        map_live_pattern,
        maps_movement_direct_proof_runner,
        product_store,
        reviews,
        routing,
        routing_federation,
        travel_marketplace,
    )

    route_state = routing.status()
    live_state = map_live_pattern.status()
    place_state = atlas_live_sources.status()
    federation_state = routing_federation.status()
    media_state = listing_media.status()
    merchant_state = certification.status()
    market_state = product_store.status()
    reviews_state = reviews.status()
    route_matrix_state = maps_movement_direct_proof_runner.route_matrix_status()
    try:
        event_state = travel_marketplace.public_offers(category="event", limit=1)
    except Exception:  # noqa: BLE001
        event_state = {"ready": False, "count": 0, "offers": []}

    road_tiles_proven = bool(
        route_state.get("runtime_verified")
        and route_state.get("oap_owned_endpoint")
        and route_state.get("road_vector_tiles")
    )
    route_geometry_proven = bool(
        route_state.get("runtime_verified")
        and route_state.get("oap_owned_endpoint")
        and route_state.get("geometry_exposed")
    )
    turn_by_turn_software_ready = bool(route_geometry_proven and FEATURE_UNLOCKS["turn_by_turn_navigation"])
    live_disruption_proven = bool(live_state.get("authority_verified_feed"))
    source_backed_places_ready = bool(place_state.get("enabled"))
    opening_hours_source_proven = bool(
        int((place_state.get("last_fetch") or {}).get("opening_hours_count") or 0) > 0
        and (place_state.get("last_fetch") or {}).get("freshness") == "fresh"
    )
    event_inventory_source_proven = bool(
        event_state.get("ready") and int(event_state.get("count") or 0) > 0
    )
    first_party_listing_photo_proven = bool(
        media_state.get("schema_ready") and int(media_state.get("photo_count") or 0) > 0
    )
    business_owner_listing_tools_ready = bool(
        market_state.get("ready")
        and merchant_state.get("runtime_ready")
        and merchant_state.get("roles_ready")
    )
    war_room_proof_runner_pass = bool(route_matrix_state.get("certified"))
    open_now_evaluator_ready = True
    connected_shards = int(federation_state.get("connected_shard_count") or 0)
    wider_uk_routing_live = bool(
        federation_state.get("uk_wide_owned_graph_proven") or connected_shards > 1
    )

    remaining = []
    if not road_tiles_proven:
        remaining.append("first-party road vector tile runtime proof")
    if not route_geometry_proven:
        remaining.append("first-party route geometry runtime proof")
    if not turn_by_turn_software_ready:
        remaining.append("turn-by-turn navigation software proof")
    if not live_disruption_proven:
        remaining.append("current authority-backed disruption feed proof")
    if not source_backed_places_ready:
        remaining.append("source-backed place lookup enablement")
    if not wider_uk_routing_live:
        remaining.append("UK-wide owned routing shard coverage")
    if not event_inventory_source_proven:
        remaining.append("source-backed event inventory proof")
    if not opening_hours_source_proven:
        remaining.append("opening-hours source proof")
    if not first_party_listing_photo_proven:
        remaining.append("first-party listing photo proof")
    if not business_owner_listing_tools_ready:
        remaining.append("business owner listing tools")
    if not war_room_proof_runner_pass:
        remaining.append("combined War Room proof-runner pass")
    first_party_reviews_ready = bool(reviews_state.get("ready"))
    if not first_party_reviews_ready:
        remaining.append("first-party reviews proof")

    software_navigation_green = bool(
        road_tiles_proven and route_geometry_proven and turn_by_turn_software_ready
    )
    london_live_pattern_green = bool(live_disruption_proven)
    overall_green = bool(not remaining)

    return {
        "road_vector_tiles_proven": road_tiles_proven,
        "route_geometry_proven": route_geometry_proven,
        "turn_by_turn_software_ready": turn_by_turn_software_ready,
        "voice_turn_guidance_ready": bool(turn_by_turn_software_ready and FEATURE_UNLOCKS["voice_turn_guidance"]),
        "off_route_reroute_ready": bool(turn_by_turn_software_ready and FEATURE_UNLOCKS["off_route_reroute"]),
        "live_disruption_authority_proven": live_disruption_proven,
        "source_backed_places_enabled": source_backed_places_ready,
        "opening_hours_source_proven": opening_hours_source_proven,
        "event_inventory_source_proven": event_inventory_source_proven,
        "first_party_listing_photo_proven": first_party_listing_photo_proven,
        "open_now_evaluator_ready": open_now_evaluator_ready,
        "business_owner_listing_tools_ready": business_owner_listing_tools_ready,
        "war_room_proof_runner_pass": war_room_proof_runner_pass,
        "first_party_reviews_ready": first_party_reviews_ready,
        "connected_routing_shards": connected_shards,
        "wider_uk_routing_live": wider_uk_routing_live,
        "software_navigation_green": software_navigation_green,
        "london_live_pattern_green": london_live_pattern_green,
        "overall_green": overall_green,
        "remaining_before_green": tuple(remaining),
    }


def local_map(query: object = None, *, category: object = None, start: object = None, end: object = None, profile: object = "driving") -> dict[str, object]:
    generated_at = _now()
    area_key = canonical(query or start or "Mitcham")
    points = points_for(area_key, category=category)
    route = route_proof(start or area_key, end or "London Bridge", profile=profile)
    return {
        "component": PROGRAMS["places"],
        "parent": PROGRAMS["map_intelligence"],
        "programs": PROGRAMS,
        "mode": "uk_first_map_intelligence_places_travel_movement",
        "query": str(query or area_key),
        "area_key": area_key,
        "country_scope": "United Kingdom",
        "generated_at": generated_at,
        "public": True,
        "brand_style": "OAP cockpit map",
        "third_party_branding_used": False,
        "public_noise_removed": True,
        "map_intelligence": MAP_INTELLIGENCE_STRUCTURE,
        "map_seeing_layers": MAP_SEEING_LAYERS,
        "sections": {
            "maps": PROGRAMS["places"],
            "inside_map_intelligence": {
                "base_map": "Base map / open geometry",
                "places": PROGRAMS["places"],
                "travel": PROGRAMS["travel"],
                "movement": PROGRAMS["movement"],
                "route": PROGRAMS["routes"],
                "direct": PROGRAMS["direct"],
                "ride": PROGRAMS["ride"],
                "drop": PROGRAMS["drop"],
                "spots": "Spots",
                "events": PROGRAMS["pattern"],
                "proof": "Proof layer",
                "consent": "Consent layer",
                "green_gate": "Green Gate",
            },
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
        "readiness": readiness_state(),
        "missing_before_green": readiness_state()["remaining_before_green"],
    }


def status() -> dict[str, object]:
    sample = local_map("Mitcham")
    readiness = readiness_state()
    return {
        "component": "Map Intelligence Status",
        "programs": PROGRAMS,
        "country_scope": "United Kingdom",
        "public_surface": "/atlas",
        "preferred_public_surface": "/on-any-place",
        "compatibility_surfaces": ("/atlas", "/uk-map", "/business-map", "/traffic-map"),
        "place_api": "/atlas/api/local-map",
        "route_proof_api": "/movement/route-proof",
        "request_preview_api": "/movement/request-preview",
        "map_intelligence": MAP_INTELLIGENCE_STRUCTURE,
        "map_seeing_layers": MAP_SEEING_LAYERS,
        "travel_inside_map_intelligence": True,
        "movement_inside_map_intelligence": True,
        "feature_unlocks": FEATURE_UNLOCKS,
        "point_count": len(LOCAL_POINTS),
        "category_count": len(UK_CATEGORIES),
        "traffic_signal_count": len(TRAFFIC_SIGNALS),
        "sample_area": sample["area_key"],
        "payment_capture_enabled": False,
        "automatic_dispatch_enabled": False,
        "hidden_tracking_enabled": False,
        "live_traffic_claim": bool(readiness["live_disruption_authority_proven"]),
        "software_navigation_green": bool(readiness["software_navigation_green"]),
        "road_vector_tiles_proven": bool(readiness["road_vector_tiles_proven"]),
        "route_geometry_proven": bool(readiness["route_geometry_proven"]),
        "turn_by_turn_software_ready": bool(readiness["turn_by_turn_software_ready"]),
        "voice_turn_guidance_ready": bool(readiness["voice_turn_guidance_ready"]),
        "off_route_reroute_ready": bool(readiness["off_route_reroute_ready"]),
        "live_disruption_authority_proven": bool(readiness["live_disruption_authority_proven"]),
        "connected_routing_shards": int(readiness["connected_routing_shards"]),
        "wider_uk_routing_live": bool(readiness["wider_uk_routing_live"]),
        "overall_green": bool(readiness["overall_green"]),
        "remaining_before_green": readiness["remaining_before_green"],
        "reason_not_green": (
            "All On Any Place Green gates are proven."
            if readiness["overall_green"]
            else "Remaining proof: " + "; ".join(readiness["remaining_before_green"])
        ),
    }
