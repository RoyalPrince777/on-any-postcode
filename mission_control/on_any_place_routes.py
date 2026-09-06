"""Approved public address protocol for the On Any Place family.

Do not change approved addresses without Founder instruction. The public UI shows
one canonical map door: /on-any-place. Older or secondary routes remain quiet
compatibility aliases so existing links do not break, but they are not promoted
as duplicate public doors.
"""
from __future__ import annotations

from flask import Blueprint, make_response, redirect, render_template, request

from . import local_map_intelligence

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
    elif path.endswith(("on-any-route", "routes")):
        values.setdefault("category", "routes")
    elif path.endswith("travel"):
        values.setdefault("category", "travel_requests")
    elif path.endswith(("on-any-ride", "ride")):
        values.setdefault("profile", "ride")
        values.setdefault("category", "ride_requests")
    elif path.endswith(("on-any-drop", "drop")):
        values.setdefault("profile", "drop")
        values.setdefault("category", "drop_requests")
    elif path.endswith("live-pattern"):
        values.setdefault("category", "traffic_signals")
    return values


@bp.get("/on-any-place")
def canonical_on_any_place():
    """Render the approved On Any Place address without changing the URL."""

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
@bp.get("/travel")
@bp.get("/on-any-ride")
@bp.get("/ride")
@bp.get("/on-any-drop")
@bp.get("/drop")
@bp.get("/live-pattern")
def quiet_program_aliases():
    """Keep old program addresses working without promoting duplicates."""

    values = _with_defaults(request.path.rstrip("/"))
    query = "&".join(f"{key}={value}" for key, value in values.items() if value is not None)
    target = "/on-any-place" + (f"?{query}" if query else "")
    return redirect(target, code=302)
