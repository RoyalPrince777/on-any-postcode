"""Founder-only Ecosystem Intelligence surface.

The dashboard exposes the constitutional model and accepts only explicit Founder
signal packs for bounded analysis. It never invents live values or persists a
fake current state when no real signal pack has been supplied.
"""

from __future__ import annotations

from flask import Blueprint, jsonify, make_response, render_template, request

from . import ecosystem_intelligence, web_security

bp = Blueprint(
    "ecosystem_intelligence",
    __name__,
    url_prefix="/mission/intelligence/ecosystem",
    template_folder="templates",
)


def _no_store(response):
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    return response


@bp.get("")
@bp.get("/")
@web_security.login_required(founder_only=True)
def dashboard():
    """Render the real-data-only Ecosystem Intelligence command view."""

    return _no_store(
        make_response(
            render_template(
                "ecosystem_intelligence.html",
                ecosystem=ecosystem_intelligence.status(),
                analysis=None,
            )
        )
    )


@bp.get("/status")
@web_security.login_required(api=True, founder_only=True)
def status():
    """Return the bounded Ecosystem Intelligence contract."""

    return _no_store(make_response(jsonify(ecosystem_intelligence.status())))


@bp.post("/analyse")
@web_security.login_required(api=True, founder_only=True)
def analyse():
    """Analyse an explicit real signal pack without performing external action."""

    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return _no_store(make_response(jsonify({"error": "json_object_required"}), 400))

    signals = payload.get("signals")
    if not isinstance(signals, list) or not signals:
        return _no_store(make_response(jsonify({"error": "signals_required"}), 400))

    try:
        result = ecosystem_intelligence.analyse(
            signals,
            scope=str(payload.get("scope") or "OAP World"),
            pressure_scores=(
                payload.get("pressure_scores")
                if isinstance(payload.get("pressure_scores"), dict)
                else None
            ),
        )
    except ValueError as exc:
        return _no_store(
            make_response(jsonify({"error": "invalid_ecosystem_signal", "detail": str(exc)}), 400)
        )

    return _no_store(make_response(jsonify(result)))
