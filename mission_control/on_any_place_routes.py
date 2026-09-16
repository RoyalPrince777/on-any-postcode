"""Canonical public Map Intelligence routes.

One public map door. Compatibility aliases stay quiet. Town/postcode suggestions
are resolved server-side so the map can autocomplete without exposing provider
calls in the browser.
"""
from __future__ import annotations

from urllib import parse as urlparse

from flask import Blueprint, jsonify, make_response, redirect, render_template, request

from . import local_map_intelligence, location_intelligence

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
        values.setdefault("profile", "ride")
        values.setdefault("category", "ride_requests")
    elif path.endswith("on-any-drop") or path.endswith("drop"):
        values.setdefault("profile", "drop")
        values.setdefault("category", "drop_requests")
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
    except Exception:
        return []
    results = payload.get("results")
    if not isinstance(results, list):
        return []
    suggestions = []
    for item in results[:8]:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or "").strip()
        country = str(item.get("country") or "").strip()
        admin = str(item.get("admin1") or item.get("admin2") or "").strip()
        if not name:
            continue
        label = ", ".join(part for part in (name, admin, country) if part)
        suggestions.append(
            {
                "label": label,
                "value": name,
                "country": country,
                "latitude": item.get("latitude"),
                "longitude": item.get("longitude"),
            }
        )
    return suggestions


@bp.get("/map-intelligence/suggest")
def map_intelligence_suggest():
    """Return bounded town/place autocomplete suggestions for Map Intelligence."""
    response = jsonify({"suggestions": _place_suggestions(request.args.get("q", ""))})
    response.headers["Cache-Control"] = "private, max-age=60"
    return response


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
    target = "/on-any-place" + (f"?{query}" if query else "")
    return redirect(target, code=302)
