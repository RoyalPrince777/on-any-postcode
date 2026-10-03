"""Authenticated OAP Ride payment binding APIs."""
from __future__ import annotations
from flask import Blueprint, jsonify, make_response, request
from . import oap_ride_payment_bridge, web_security

bp=Blueprint("oap_ride_payment_bridge_routes",__name__)

def _no_store(r):
    r.headers["Cache-Control"]="no-store, private"; r.headers["X-Content-Type-Options"]="nosniff"; return r
def _error(code,status): return _no_store(make_response(jsonify(error={"code":code}),status))
def _body():
    value=request.get_json(silent=True)
    if not isinstance(value,dict): raise TypeError("json_object_required")
    return value
def _translate(exc):
    if isinstance(exc,PermissionError): return _error(str(exc) or "ride_payment_denied",403)
    if isinstance(exc,(TypeError,ValueError)): return _error(str(exc) or "invalid_ride_payment_request",400)
    return _error("ride_payment_bridge_unavailable",503)
def _identity(): return web_security.authenticated_identity()
def _guard(identity):
    if not web_security.csrf_valid(request): return _error("csrf_failed",403)
    if not web_security.PUBLIC_WRITE_LIMITER.allow(identity): return _error("rate_limited",429)
    return None

@bp.post("/transport/ride/bookings/<booking_id>/sika-payment")
@web_security.login_required(api=True)
def bind_payment(booking_id:str):
    identity=_identity()
    if g:=_guard(identity): return g
    try:
        body=_body()
        result=oap_ride_payment_bridge.bind(
            booking_id=booking_id,rider_identity_id=identity,payment_id=body.get("payment_id")
        )
        return _no_store(make_response(jsonify(result),200))
    except Exception as exc: return _translate(exc)

@bp.get("/transport/ride/bookings/<booking_id>/sika-payment")
@web_security.login_required(api=True)
def payment_projection(booking_id:str):
    try:
        result=oap_ride_payment_bridge.projection(booking_id=booking_id)
        return _no_store(make_response(jsonify(result),200))
    except Exception as exc: return _translate(exc)
