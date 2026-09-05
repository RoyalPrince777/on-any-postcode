"""Clean public aliases for the On Any Place program family."""
from __future__ import annotations

from flask import Blueprint, redirect, request, url_for

bp = Blueprint("on_any_place", __name__)


@bp.get("/on-any-place")
@bp.get("/on-any-route")
@bp.get("/on-any-ride")
@bp.get("/on-any-drop")
@bp.get("/live-pattern")
def public_program_aliases():
    """Redirect clean program URLs to the current cockpit surface safely."""

    endpoint = "travel_supply.public_atlas"
    values = dict(request.args)
    if request.path.endswith("on-any-ride"):
        values.setdefault("profile", "ride")
        values.setdefault("category", "ride_requests")
    elif request.path.endswith("on-any-drop"):
        values.setdefault("profile", "drop")
        values.setdefault("category", "drop_requests")
    elif request.path.endswith("live-pattern"):
        values.setdefault("category", "traffic_signals")
    return redirect(url_for(endpoint, **values), code=302)
