"""Canonical public Map Intelligence routes.

One public map door. Town/postcode suggestions, source-backed places and
read-only OAP-owned routing are exposed here. Booking remains separate.
"""
from __future__ import annotations

from urllib import parse as urlparse

from flask import Blueprint, jsonify, make_response, redirect, render_template, request

from . import (
    atlas_live_sources,
    local_map_intelligence,
    location_intelligence,
    map_live_pattern,
    routing,
    routing_federation,
    web_security,
)

bp = Blueprint("on_any_place", __name__)


def _no_store(response):
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


def _with_defaults(path: str) -> dict[str, object]:
    values = dict(request.args)
    if path.endswith("spots"):
        values.setdefault("category", "spots")
    elif path.endswith("events"):
        values.setdefault("category", "events")
    elif path.endswith("on-any-route") or path.endswith("routes"):
        values.setdefault("category", "routes")
    elif path.endswith("on-any-ride") or path.endswith("ride"):
        values.setdefault("profile", "ride"); values.setdefault("category", "ride_requests")
    elif path.endswith("on-any-drop") or path.endswith("drop"):
        values.setdefault("profile", "drop"); values.setdefault("category", "drop_requests")
    elif path.endswith("live-pattern"):
        values.setdefault("category", "traffic_signals")
    return values


def _place_suggestions(query: str) -> list[dict[str, object]]:
    term = " ".join(str(query or "").strip().split())[:80]
    if len(term) < 2:
        return []
    params = urlparse.urlencode({"name": term, "count": 8, "language": "en", "format": "json"})
    try:
        payload = location_intelligence._json(
            "https://geocoding-api.open-meteo.com/v1/search?" + params,
            "geocoding-api.open-meteo.com",
        )
    except (ValueError, location_intelligence.LocationUnavailable):
        return []
    results = payload.get("results")
    if not isinstance(results, list):
        return []
    suggestions: list[dict[str, object]] = []
    for item in results[:8]:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or "").strip()
        country = str(item.get("country") or "").strip()
        admin = str(item.get("admin1") or item.get("admin2") or "").strip()
        if not name:
            continue
        suggestions.append({
            "label": ", ".join(part for part in (name, admin, country) if part),
            "value": name,
            "country": country,
            "latitude": item.get("latitude"),
            "longitude": item.get("longitude"),
        })
    return suggestions


def _road_sequence(route: dict[str, object]) -> list[str]:
    roads: list[str] = []
    for step in route.get("steps", []) if isinstance(route.get("steps"), list) else []:
        if not isinstance(step, dict):
            continue
        name = " ".join(str(step.get("name") or "").split())[:120]
        if name and (not roads or roads[-1] != name):
            roads.append(name)
        if len(roads) >= 30:
            break
    return roads


@bp.get("/map-intelligence/suggest")
def map_intelligence_suggest():
    response = jsonify({"suggestions": _place_suggestions(request.args.get("q", ""))})
    response.headers["Cache-Control"] = "private, max-age=60"
    return response


@bp.get("/map-intelligence/places")
def map_intelligence_places():
    query = request.args.get("q") or request.args.get("location") or "Mitcham"
    result = atlas_live_sources.fetch_places(query)
    response = jsonify({
        "component": "Map Intelligence Places",
        "query": result.get("query"),
        "results": result.get("results", []),
        "result_count": result.get("result_count", 0),
        "source": result.get("adapter"),
        "source_timestamp": result.get("fetched_at"),
        "attribution": result.get("attribution"),
        "freshness": "timestamped" if result.get("fetched_at") else "unavailable",
        "source_backed": bool(result.get("can_claim_live_now")),
        "hidden_tracking": False,
        "payment_capture": False,
        "dispatch": False,
    })
    response.headers["Cache-Control"] = "no-store"
    return response


@bp.get("/map-intelligence/live-pattern")
def map_intelligence_live_pattern():
    query = request.args.get("q") or request.args.get("location") or ""
    response = jsonify({
        "component": "OAP Live Pattern",
        "reports": map_live_pattern.reports(query),
        "status": map_live_pattern.status(),
        "authority_verified_feed": False,
        "advisory_only": True,
        "automatic_rerouting": False,
    })
    response.headers["Cache-Control"] = "no-store"
    return response


@bp.post("/map-intelligence/live-pattern")
def map_intelligence_live_pattern_report():
    if not web_security.csrf_valid(request):
        return jsonify({"error": {"code": "csrf_failed"}}), 403
    payload = request.get_json(silent=True) if request.is_json else request.form
    try:
        report = map_live_pattern.add_report(
            area=payload.get("area"),
            road=payload.get("road"),
            kind=payload.get("kind"),
            note=payload.get("note"),
        )
    except ValueError as exc:
        return jsonify({"error": {"code": str(exc)[:80]}}), 400
    response = jsonify({"report": report, "advisory_only": True, "authority_verified": False})
    response.headers["Cache-Control"] = "no-store"
    return response, 201


@bp.get("/map-intelligence/status")
def map_intelligence_status():
    route_status = routing.status()
    federation_status = routing_federation.status()
    place_status = atlas_live_sources.status()
    return _no_store(make_response(jsonify({
        "component": "Map Intelligence",
        "routing_provider": route_status.get("provider_ownership"),
        "routing_runtime_verified": route_status.get("runtime_verified"),
        "route_geometry": bool(route_status.get("geometry_exposed")),
        "turn_by_turn": True,
        "autocomplete": True,
        "source_backed_places_enabled": bool(place_status.get("enabled")),
        "live_pattern": map_live_pattern.status(),
        "routing_federation": federation_status,
        "coverage": {
            "current_graph": "Greater London",
            "scope": "greater_london_first_party_slice",
            "wider_coverage_architecture_ready": bool(federation_status.get("ready_for_additional_owned_shards")),
            "wider_coverage_live": False,
        },
        "public_fallback_enabled": False,
        "booking_separate": True,
        "payment_capture": False,
        "dispatch": False,
    })))


@bp.get("/map-intelligence/route")
def map_intelligence_route():
    origin = " ".join(str(request.args.get("from") or request.args.get("location") or "").strip().split())[:120]
    destination = " ".join(str(request.args.get("to") or "").strip().split())[:120]
    profile = str(request.args.get("profile") or "driving")[:20]
    if len(origin) < 2 or len(destination) < 2:
        return jsonify({"error": {"code": "route_places_required"}}), 400
    try:
        start = location_intelligence.lookup(origin)
        end = location_intelligence.lookup(destination)
        coverage = routing_federation.coverage_state(start, end)
        if not coverage["route_expected"]:
            response = jsonify({
                "error": {"code": "outside_current_oap_map_coverage"},
                "coverage": coverage,
                "origin": {"label": origin, "country": start.get("country")},
                "destination": {"label": destination, "country": end.get("country")},
            })
            response.headers["Cache-Control"] = "no-store"
            return response, 422
        result = routing_federation.map_route(start=start, end=end, profile=profile)
    except ValueError as exc:
        return jsonify({"error": {"code": str(exc)[:80]}}), 400
    except (location_intelligence.LocationUnavailable, routing.RoutingUnavailable) as exc:
        return jsonify({"error": {"code": str(exc)[:100] or "map_route_unavailable"}}), 503
    result["roads"] = _road_sequence(result)
    result["live_pattern_reports"] = map_live_pattern.reports(destination)
    response = jsonify({
        "route": result,
        "coverage": coverage,
        "origin": {"label": origin, "postcode": start.get("postcode"), "borough": start.get("borough"), "county": start.get("county"), "country": start.get("country"), "latitude": start.get("latitude"), "longitude": start.get("longitude")},
        "destination": {"label": destination, "postcode": end.get("postcode"), "borough": end.get("borough"), "county": end.get("county"), "country": end.get("country"), "latitude": end.get("latitude"), "longitude": end.get("longitude")},
        "operational_dispatch": False,
        "payment_capture": False,
        "hidden_tracking": False,
    })
    response.headers["Cache-Control"] = "no-store"
    return response


@bp.get("/booking")
def booking_entry():
    return redirect("/travel/direct", code=302)


@bp.get("/on-any-place")
def canonical_on_any_place():
    values = _with_defaults(request.path.rstrip("/"))
    local_map = local_map_intelligence.local_map(
        values.get("location") or values.get("area") or "Mitcham",
        category=values.get("category") or "all",
        start=values.get("from"),
        end=values.get("to") or "London Bridge",
        profile=values.get("profile") or "driving",
    )
    return _no_store(make_response(render_template("local_map.html", local_map=local_map)))


@bp.get("/places")
@bp.get("/spots")
@bp.get("/events")
@bp.get("/on-any-route")
@bp.get("/routes")
@bp.get("/on-any-ride")
@bp.get("/ride")
@bp.get("/on-any-drop")
@bp.get("/drop")
@bp.get("/live-pattern")
def quiet_program_aliases():
    values = _with_defaults(request.path.rstrip("/"))
    query = "&".join(f"{key}={value}" for key, value in values.items() if value is not None)
    return redirect("/on-any-place" + (f"?{query}" if query else ""), code=302)
