"""Founder-only OAP ISAC Spatial Intelligence web surface."""

from __future__ import annotations

from flask import Blueprint, jsonify, make_response, render_template, request

from . import isac_spatial_intelligence, web_security

bp = Blueprint("isac_spatial", __name__)


def _no_store(response):
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


def _error(code: str, message: str, status_code: int):
    return _no_store(
        make_response(jsonify(error={"code": code, "message": message}), status_code)
    )


@bp.get("")
@web_security.login_required(founder_only=True)
def dashboard():
    """Render current spatial intelligence state without inventing radio data."""

    response = make_response(
        render_template(
            "isac_spatial.html",
            isac=isac_spatial_intelligence.isac_spatial_status(),
        )
    )
    return _no_store(response)


@bp.get("/status")
@web_security.login_required(api=True, founder_only=True)
def status():
    """Return read-only ISAC readiness and privacy-reduced spatial state."""

    return _no_store(
        make_response(jsonify(isac_spatial_intelligence.isac_spatial_status()))
    )


@bp.post("/ingest")
@web_security.login_required(api=True, founder_only=True)
def ingest():
    """Founder-authorised development ingest for SRS/CSI adapter payloads."""

    if not web_security.csrf_valid(request):
        return _error("csrf_failed", "The secure session expired.", 403)
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return _error("invalid_request", "A JSON object is required.", 400)
    try:
        result = isac_spatial_intelligence.ingest_authorised_payload(payload)
    except PermissionError:
        return _error(
            "rf_measurement_not_authorised",
            "Explicit authorised=true is required for RF measurement ingestion.",
            403,
        )
    except (TypeError, ValueError) as exc:
        return _error("invalid_rf_measurement", str(exc)[:120], 400)
    return _no_store(make_response(jsonify(result)))


@bp.post("/calibrate")
@web_security.login_required(api=True, founder_only=True)
def calibrate():
    """Add one explicit local calibration observation; never infer coordinates."""

    if not web_security.csrf_valid(request):
        return _error("csrf_failed", "The secure session expired.", 403)
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return _error("invalid_request", "A JSON object is required.", 400)
    try:
        result = isac_spatial_intelligence.add_authorised_calibration(payload)
    except PermissionError:
        return _error(
            "rf_measurement_not_authorised",
            "Explicit authorised=true is required for calibration RF data.",
            403,
        )
    except (TypeError, ValueError) as exc:
        return _error("invalid_calibration", str(exc)[:120], 400)
    return _no_store(make_response(jsonify(result)))
