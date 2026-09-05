"""Founder-only OAP ISAC Spatial Intelligence and Spatial Presence web surfaces."""

from __future__ import annotations

from flask import Blueprint, jsonify, make_response, render_template, request

from . import isac_spatial_intelligence, spatial_presence, web_security

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
    response = make_response(
        render_template(
            "isac_spatial.html",
            isac=isac_spatial_intelligence.isac_spatial_status(),
        )
    )
    return _no_store(response)


@bp.get("/app")
@web_security.login_required(founder_only=True)
def app_dashboard():
    response = make_response(
        render_template(
            "isac_app.html",
            isac=isac_spatial_intelligence.isac_app_status(),
            oap_csrf_token=web_security.csrf_token(),
        )
    )
    return _no_store(response)


@bp.get("/status")
@web_security.login_required(api=True, founder_only=True)
def status():
    return _no_store(make_response(jsonify(isac_spatial_intelligence.isac_spatial_status())))


@bp.get("/app/status")
@web_security.login_required(api=True, founder_only=True)
def app_status():
    return _no_store(make_response(jsonify(isac_spatial_intelligence.isac_app_status())))


@bp.post("/app/proof-check")
@web_security.login_required(api=True, founder_only=True)
def app_proof_check():
    if not web_security.csrf_valid(request):
        return _error("csrf_failed", "The secure session expired.", 403)
    return _no_store(make_response(jsonify(isac_spatial_intelligence.run_isac_proof_check())))


@bp.post("/app/seed-software-test")
@web_security.login_required(api=True, founder_only=True)
def app_seed_software_test():
    if not web_security.csrf_valid(request):
        return _error("csrf_failed", "The secure session expired.", 403)
    return _no_store(make_response(jsonify(isac_spatial_intelligence.seed_software_app_test())))


@bp.post("/ingest")
@web_security.login_required(api=True, founder_only=True)
def ingest():
    if not web_security.csrf_valid(request):
        return _error("csrf_failed", "The secure session expired.", 403)
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return _error("invalid_request", "A JSON object is required.", 400)
    try:
        result = isac_spatial_intelligence.ingest_authorised_payload(payload)
    except PermissionError:
        return _error("rf_measurement_not_authorised", "Explicit authorised=true is required for RF measurement ingestion.", 403)
    except (TypeError, ValueError) as exc:
        return _error("invalid_rf_measurement", str(exc)[:120], 400)
    return _no_store(make_response(jsonify(result)))


@bp.post("/calibrate")
@web_security.login_required(api=True, founder_only=True)
def calibrate():
    if not web_security.csrf_valid(request):
        return _error("csrf_failed", "The secure session expired.", 403)
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return _error("invalid_request", "A JSON object is required.", 400)
    try:
        result = isac_spatial_intelligence.add_authorised_calibration(payload)
    except PermissionError:
        return _error("rf_measurement_not_authorised", "Explicit authorised=true is required for calibration RF data.", 403)
    except (TypeError, ValueError) as exc:
        return _error("invalid_calibration", str(exc)[:120], 400)
    return _no_store(make_response(jsonify(result)))


@bp.get("/presence")
@web_security.login_required(founder_only=True)
def spatial_presence_dashboard():
    return _no_store(
        make_response(
            render_template(
                "spatial_presence.html",
                presence=spatial_presence.spatial_presence_status(),
            )
        )
    )


@bp.get("/presence/status")
@web_security.login_required(api=True, founder_only=True)
def spatial_presence_status():
    return _no_store(make_response(jsonify(spatial_presence.spatial_presence_status())))


@bp.post("/presence/session")
@web_security.login_required(api=True, founder_only=True)
def spatial_presence_session():
    if not web_security.csrf_valid(request):
        return _error("csrf_failed", "The secure session expired.", 403)
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return _error("invalid_request", "A JSON object is required.", 400)
    try:
        result = spatial_presence.create_session(payload)
    except PermissionError:
        return _error("capture_consent_required", "Explicit participant capture consent is required.", 403)
    except (TypeError, ValueError) as exc:
        return _error("invalid_spatial_session", str(exc)[:120], 400)
    return _no_store(make_response(jsonify(result)))


@bp.delete("/presence/session/<session_id>")
@web_security.login_required(api=True, founder_only=True)
def spatial_presence_end_session(session_id: str):
    if not web_security.csrf_valid(request):
        return _error("csrf_failed", "The secure session expired.", 403)
    return _no_store(make_response(jsonify(spatial_presence.end_session(session_id))))
