"""Founder-only International Humanitarian Emergency Tracker surface."""

from __future__ import annotations

from flask import Blueprint, jsonify, make_response, render_template, request

from . import humanitarian_emergency_tracker, web_security

bp = Blueprint("humanitarian_tracker", __name__)


def _no_store(response):
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


@bp.get("")
@web_security.login_required(founder_only=True)
def dashboard():
    """Render the current authoritative civilian emergency snapshot."""

    snapshot = humanitarian_emergency_tracker.humanitarian_emergency_snapshot()
    return _no_store(
        make_response(
            render_template(
                "humanitarian_emergency_tracker.html",
                tracker=snapshot,
            )
        )
    )


@bp.get("/status")
@web_security.login_required(api=True, founder_only=True)
def status():
    """Return a bounded live snapshot; refresh=1 bypasses the short source cache."""

    force = request.args.get("refresh", "").strip().casefold() in {"1", "true", "yes"}
    snapshot = humanitarian_emergency_tracker.humanitarian_emergency_snapshot(force=force)
    return _no_store(make_response(jsonify(snapshot)))
