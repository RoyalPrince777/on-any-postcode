"""Authenticated OAP Ride Guardian APIs."""
from __future__ import annotations
from flask import Blueprint, jsonify, make_response, request
from . import oap_ride_guardian, web_security

bp=Blueprint("oap_ride_guardian_routes",__name__)

def _no_store(r):
    r.headers["Cache-Control"]="no-store, private"; r.headers["X-Content-Type-Options"]="nosniff"; return r
def _error(code,status): return _no_store(make_response(jsonify(error={"code":code}),status))
def _body():
    value=request.get_json(silent=True)
    if not isinstance(value,dict): raise TypeError("json_object_required")
    return value
def _translate(exc):
    if isinstance(exc,PermissionError): return _error(str(exc) or "ride_guardian_denied",403)
    if isinstance(exc,(TypeError,ValueError)): return _error(str(exc) or "invalid_guardian_request",400)
    return _error("ride_guardian_unavailable",503)
def _identity(): return web_security.authenticated_identity()
def _guard(identity):
    if not web_security.csrf_valid(request): return _error("csrf_failed",403)
    if not web_security.PUBLIC_WRITE_LIMITER.allow(identity): return _error("rate_limited",429)
    return None

@bp.get("/transport/ride/guardian/status")
@web_security.login_required(api=True)
def guardian_status():
    return _no_store(make_response(jsonify(oap_ride_guardian.status()),200))

@bp.post("/transport/ride/bookings/<booking_id>/guardian")
@web_security.login_required(api=True)
def guardian_session(booking_id:str):
    identity=_identity()
    if g:=_guard(identity): return g
    try:
        body=_body()
        result=oap_ride_guardian.set_session(
            booking_id=booking_id,identity_id=identity,
            enabled=body.get("enabled"),trusted_contact_ref=body.get("trusted_contact_ref","")
        )
        return _no_store(make_response(jsonify(result),200))
    except Exception as exc: return _translate(exc)

@bp.post("/transport/ride/bookings/<booking_id>/guardian/incidents")
@web_security.login_required(api=True)
def guardian_incident(booking_id:str):
    identity=_identity()
    if g:=_guard(identity): return g
    try:
        body=_body()
        result=oap_ride_guardian.report_incident(
            booking_id=booking_id,identity_id=identity,
            kind=body.get("kind"),note=body.get("note","")
        )
        return _no_store(make_response(jsonify(result),201))
    except Exception as exc: return _translate(exc)


@bp.post("/transport/ride/bookings/<booking_id>/guardian/analyse")
@web_security.login_required(api=True)
def guardian_analyse(booking_id:str):
    identity=_identity()
    if g:=_guard(identity): return g
    try:
        body=request.get_json(silent=True) or {}
        result=oap_ride_guardian.analyse_tracking(
            booking_id=booking_id,
            identity_id=identity,
            stop_minutes=body.get("stop_minutes",8),
            stop_radius_m=body.get("stop_radius_m",40),
        )
        return _no_store(make_response(jsonify(result),200))
    except Exception as exc: return _translate(exc)
