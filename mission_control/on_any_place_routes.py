"""Canonical public Map Intelligence routes.

One public map door. Compatibility aliases stay quiet. Town/postcode suggestions
and explicit route searches are resolved server-side. Booking remains separate.
"""
from __future__ import annotations

from urllib import parse as urlparse

from flask import Blueprint, jsonify, make_response, redirect, render_template, request

from . import local_map_intelligence, location_intelligence, routing

bp = Blueprint("on_any_place", __name__)

# Truthful coverage declaration for the currently loaded first-party OSRM graph.
GREATER_LONDON_BOUNDS = {
    "min_lat": 51.28,
    "max_lat": 51.70,
    "min_lon": -0.52,
    "max_lon": 0.34,
}


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
    params = urlparse.urlencode({"name":term,"count":8,"language":"en","format":"json"})
    try:
        payload = location_intelligence._json("https://geocoding-api.open-meteo.com/v1/search?"+params,"geocoding-api.open-meteo.com")
    except (ValueError, location_intelligence.LocationUnavailable):
        return []
    results = payload.get("results")
    if not isinstance(results, list):
        return []
    suggestions=[]
    for item in results[:8]:
        if not isinstance(item,dict): continue
        name=str(item.get("name") or "").strip(); country=str(item.get("country") or "").strip(); admin=str(item.get("admin1") or item.get("admin2") or "").strip()
        if not name: continue
        label=", ".join(part for part in (name,admin,country) if part)
        suggestions.append({"label":label,"value":name,"country":country,"latitude":item.get("latitude"),"longitude":item.get("longitude")})
    return suggestions


def _inside_current_coverage(place: dict[str, object]) -> bool:
    try:
        lat = float(place.get("latitude"))
        lon = float(place.get("longitude"))
    except (TypeError, ValueError):
        return False
    return (
        GREATER_LONDON_BOUNDS["min_lat"] <= lat <= GREATER_LONDON_BOUNDS["max_lat"]
        and GREATER_LONDON_BOUNDS["min_lon"] <= lon <= GREATER_LONDON_BOUNDS["max_lon"]
    )


def _coverage_state(start: dict[str, object], end: dict[str, object]) -> dict[str, object]:
    start_in = _inside_current_coverage(start)
    end_in = _inside_current_coverage(end)
    return {
        "current_graph": "Greater London",
        "origin_in_coverage": start_in,
        "destination_in_coverage": end_in,
        "route_expected": start_in and end_in,
        "scope": "greater_london_first_party_slice",
        "wider_coverage_ready": False,
    }


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
    response=jsonify({"suggestions":_place_suggestions(request.args.get("q",""))})
    response.headers["Cache-Control"]="private, max-age=60"
    return response


@bp.get("/map-intelligence/status")
def map_intelligence_status():
    route_status = routing.status()
    return _no_store(make_response(jsonify({
        "component": "Map Intelligence",
        "routing_provider": route_status.get("provider_ownership"),
        "routing_runtime_verified": route_status.get("runtime_verified"),
        "coverage": {
            "current_graph": "Greater London",
            "scope": "greater_london_first_party_slice",
            "wider_coverage_ready": False,
        },
        "public_fallback_enabled": False,
        "booking_separate": True,
        "payment_capture": False,
        "dispatch": False,
    })))


@bp.get("/map-intelligence/route")
def map_intelligence_route():
    """Resolve explicit places and return OAP-owned read-only route geometry."""
    origin=" ".join(str(request.args.get("from") or request.args.get("location") or "").strip().split())[:120]
    destination=" ".join(str(request.args.get("to") or "").strip().split())[:120]
    profile=str(request.args.get("profile") or "driving")[:20]
    if len(origin)<2 or len(destination)<2:
        return jsonify({"error":{"code":"route_places_required"}}),400
    try:
        start=location_intelligence.lookup(origin)
        end=location_intelligence.lookup(destination)
        coverage = _coverage_state(start, end)
        if not coverage["route_expected"]:
            response = jsonify({
                "error": {"code": "outside_current_oap_map_coverage"},
                "coverage": coverage,
                "origin": {"label": origin, "country": start.get("country")},
                "destination": {"label": destination, "country": end.get("country")},
            })
            response.headers["Cache-Control"] = "no-store"
            return response, 422
        result=routing.map_route(
            pickup_latitude=start["latitude"],pickup_longitude=start["longitude"],
            destination_latitude=end["latitude"],destination_longitude=end["longitude"],
            profile=profile,
        )
    except ValueError as exc:
        return jsonify({"error":{"code":str(exc)[:80]}}),400
    except (location_intelligence.LocationUnavailable,routing.RoutingUnavailable) as exc:
        return jsonify({"error":{"code":str(exc)[:100] or "map_route_unavailable"}}),503
    result["roads"] = _road_sequence(result)
    response=jsonify({
        "route":result,
        "coverage": coverage,
        "origin":{"label":origin,"postcode":start.get("postcode"),"borough":start.get("borough"),"county":start.get("county"),"country":start.get("country"),"latitude":start.get("latitude"),"longitude":start.get("longitude")},
        "destination":{"label":destination,"postcode":end.get("postcode"),"borough":end.get("borough"),"county":end.get("county"),"country":end.get("country"),"latitude":end.get("latitude"),"longitude":end.get("longitude")},
        "operational_dispatch":False,"payment_capture":False,"hidden_tracking":False,
    })
    response.headers["Cache-Control"]="no-store"
    return response


@bp.get("/booking")
def booking_entry():
    return redirect("/travel/direct",code=302)


@bp.get("/on-any-place")
def canonical_on_any_place():
    values=_with_defaults(request.path.rstrip("/"))
    local_map=local_map_intelligence.local_map(values.get("location") or values.get("area") or "Mitcham",category=values.get("category") or "all",start=values.get("from"),end=values.get("to") or "London Bridge",profile=values.get("profile") or "driving")
    return _no_store(make_response(render_template("local_map.html",local_map=local_map)))


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
    values=_with_defaults(request.path.rstrip("/"))
    query="&".join(f"{key}={value}" for key,value in values.items() if value is not None)
    target="/on-any-place"+(f"?{query}" if query else "")
    return redirect(target,code=302)
