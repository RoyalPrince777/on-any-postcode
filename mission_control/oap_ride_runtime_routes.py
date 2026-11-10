# ruff: noqa: BLE001
"""Authenticated OAP Ride journey lifecycle APIs."""
from __future__ import annotations

from flask import Blueprint, jsonify, make_response, request

from . import oap_ride_runtime, web_security

bp = Blueprint("oap_ride_runtime_routes", __name__)


def _no_store(response):
    response.headers["Cache-Control"] = "no-store, private"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


def _error(code: str, status: int):
    return _no_store(make_response(jsonify(error={"code": code}), status))


def _identity() -> str:
    return web_security.authenticated_identity()


def _body() -> dict:
    value = request.get_json(silent=True)
    if not isinstance(value, dict):
        raise TypeError("json_object_required")
    return value


def _guard(identity: str):
    if not web_security.csrf_valid(request):
        return _error("csrf_failed", 403)
    if not web_security.PUBLIC_WRITE_LIMITER.allow(identity):
        return _error("rate_limited", 429)
    return None


def _translate(exc: Exception):
    if isinstance(exc, PermissionError):
        return _error(str(exc) or "ride_access_denied", 403)
    if isinstance(exc, (TypeError, ValueError)):
        return _error(str(exc) or "invalid_ride_request", 400)
    return _error("ride_runtime_unavailable", 503)


@bp.get("/transport/ride/runtime/schema")
@web_security.login_required(api=True)
def ride_schema():
    return _no_store(make_response(jsonify(oap_ride_runtime.schema_status()), 200))


@bp.post("/transport/ride/bookings/<booking_id>/journey-code")
@web_security.login_required(api=True)
def issue_journey_code(booking_id: str):
    identity = _identity()
    if guarded := _guard(identity):
        return guarded
    try:
        result = oap_ride_runtime.issue_journey_code(
            booking_id=booking_id,
            rider_identity_id=identity,
        )
        return _no_store(make_response(jsonify(result), 201))
    except Exception as exc:
        return _translate(exc)


@bp.post("/transport/ride/bookings/<booking_id>/start")
@web_security.login_required(api=True)
def start_journey(booking_id: str):
    identity = _identity()
    if guarded := _guard(identity):
        return guarded
    try:
        body = _body()
        result = oap_ride_runtime.verify_and_start(
            booking_id=booking_id,
            driver_identity_id=identity,
            journey_code=body.get("journey_code"),
        )
        return _no_store(make_response(jsonify(result), 200))
    except Exception as exc:
        return _translate(exc)


@bp.post("/transport/ride/bookings/<booking_id>/complete")
@web_security.login_required(api=True)
def complete_journey(booking_id: str):
    identity = _identity()
    if guarded := _guard(identity):
        return guarded
    try:
        result = oap_ride_runtime.complete(
            booking_id=booking_id,
            driver_identity_id=identity,
        )
        return _no_store(make_response(jsonify(result), 200))
    except Exception as exc:
        return _translate(exc)


@bp.get("/transport/ride/bookings/<booking_id>/receipt")
@web_security.login_required(api=True)
def get_receipt(booking_id: str):
    identity = _identity()
    try:
        result = oap_ride_runtime.receipt(
            booking_id=booking_id,
            identity_id=identity,
        )
        return _no_store(make_response(jsonify(result), 200))
    except Exception as exc:
        return _translate(exc)


@bp.post("/transport/ride/bookings/<booking_id>/feedback")
@web_security.login_required(api=True)
def feedback(booking_id: str):
    identity = _identity()
    if guarded := _guard(identity):
        return guarded
    try:
        body = _body()
        result = oap_ride_runtime.leave_feedback(
            booking_id=booking_id,
            author_identity_id=identity,
            rating=body.get("rating"),
            note=body.get("note", ""),
        )
        return _no_store(make_response(jsonify(result), 201))
    except Exception as exc:
        return _translate(exc)
