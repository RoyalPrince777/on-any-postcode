"""Founder-only Ecosystem Intelligence surface.

The surface exposes automatic owned-runtime ingestion, explicit signal analysis,
Founder-triggered live source refreshes, full proof passes and Founder-approved
outcome receipts. It never invents external live data and never grants operational
execution.
"""
from __future__ import annotations

from flask import Blueprint, jsonify, make_response, render_template, request

from . import (
    ecosystem_intelligence,
    ecosystem_live_sources,
    ecosystem_runtime,
    location_intelligence,
    web_security,
)

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
    """Render the automatic internal Ecosystem command view."""

    return _no_store(
        make_response(
            render_template(
                "ecosystem_intelligence.html",
                ecosystem=ecosystem_intelligence.status(),
                runtime=ecosystem_runtime.current_state(),
                live_sources=ecosystem_live_sources.status(),
            )
        )
    )


@bp.get("/status")
@web_security.login_required(api=True, founder_only=True)
def status():
    return _no_store(
        make_response(
            jsonify(
                {
                    "architecture": ecosystem_intelligence.status(),
                    "runtime": ecosystem_runtime.status(),
                    "live_sources": ecosystem_live_sources.status(),
                }
            )
        )
    )


@bp.get("/live")
@web_security.login_required(api=True, founder_only=True)
def live():
    """Return automatic owned-runtime Ecosystem analysis with no network calls."""

    return _no_store(make_response(jsonify(ecosystem_runtime.current_state())))


@bp.get("/source/location-weather")
@web_security.login_required(api=True, founder_only=True)
def source_location_weather():
    """Refresh explicit Founder-supplied location/weather evidence."""

    location = str(request.args.get("location") or "").strip()
    if not location:
        return _no_store(make_response(jsonify({"error": "location_required"}), 400))
    try:
        result = ecosystem_live_sources.location_weather(location)
    except (ValueError, location_intelligence.LocationUnavailable) as exc:
        return _no_store(
            make_response(
                jsonify({"error": "live_source_unavailable", "detail": str(exc)}),
                503,
            )
        )
    return _no_store(make_response(jsonify(result)))


@bp.post("/prove-full")
@web_security.login_required(api=True, founder_only=True)
def prove_full():
    """Run one bounded proof pass over every currently available evidence lane."""

    payload = request.get_json(silent=True)
    location = ""
    if isinstance(payload, dict):
        location = str(payload.get("location") or "").strip()
    if not location:
        location = str(request.form.get("location") or "").strip()
    if not location:
        return _no_store(make_response(jsonify({"error": "location_required"}), 400))
    try:
        result = ecosystem_live_sources.prove_full(location)
    except ValueError as exc:
        return _no_store(
            make_response(jsonify({"error": "invalid_proof_request", "detail": str(exc)}), 400)
        )
    return _no_store(make_response(jsonify(result)))


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

    supplied_scores = payload.get("pressure_scores")
    pressure_scores = (
        supplied_scores
        if isinstance(supplied_scores, dict)
        else ecosystem_runtime.auto_pressure_scores(signals)
    )
    try:
        result = ecosystem_intelligence.analyse(
            signals,
            scope=str(payload.get("scope") or "OAP World"),
            pressure_scores=pressure_scores,
        )
    except (TypeError, ValueError) as exc:
        return _no_store(
            make_response(
                jsonify({"error": "invalid_ecosystem_signal", "detail": str(exc)}),
                400,
            )
        )

    result["extended_matrix_lenses"] = ecosystem_runtime.extended_matrix_lenses(signals)
    return _no_store(make_response(jsonify(result)))


@bp.post("/outcome")
@web_security.login_required(api=True, founder_only=True)
def outcome():
    """Record a Founder-approved decision outcome for HRM/RSI learning."""

    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return _no_store(make_response(jsonify({"error": "json_object_required"}), 400))
    result = ecosystem_runtime.record_outcome(
        analysis_id=str(payload.get("analysis_id") or ""),
        decision=str(payload.get("decision") or ""),
        outcome=str(payload.get("outcome") or ""),
        evidence=(payload.get("evidence") if isinstance(payload.get("evidence"), list) else ()),
        founder_approved=payload.get("founder_approved") is True,
    )
    return _no_store(make_response(jsonify(result), 200 if result["ok"] else 409))
