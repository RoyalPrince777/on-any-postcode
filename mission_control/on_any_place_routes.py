"""Clean public aliases for the On Any Place program family."""
from __future__ import annotations

from flask import Blueprint, redirect, request, url_for

bp = Blueprint("on_any_place", __name__)


@bp.get("/on-any-place")
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
def public_program_aliases():
    """Redirect clean program URLs to the current cockpit surface safely."""

    endpoint = "travel_supply.public_atlas"
    values = dict(request.args)
    path = request.path.rstrip("/")
    if path.endswith("spots"):
        values.setdefault("category", "spots")
    elif path.endswith("events"):
        values.setdefault("category", "events")
    elif path.endswith("on-any-route") or path.endswith("routes"):
        values.setdefault("category", "routes")
    elif path.endswith("travel"):
        values.setdefault("category", "transport")
    elif path.endswith("on-any-ride") or path.endswith("ride"):
        values.setdefault("profile", "ride")
        values.setdefault("category", "ride_requests")
    elif path.endswith("on-any-drop") or path.endswith("drop"):
        values.setdefault("profile", "drop")
        values.setdefault("category", "drop_requests")
    elif path.endswith("live-pattern"):
        values.setdefault("category", "live_pattern")
    return redirect(url_for(endpoint, **values), code=302)
