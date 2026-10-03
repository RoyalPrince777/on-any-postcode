# ruff: noqa: I001, BLE001
"""Authenticated OAP Ride driver accessibility APIs."""
from __future__ import annotations
from flask import Blueprint, jsonify, make_response, request
from . import oap_ride_driver_accessibility, web_security

bp=Blueprint("oap_ride_driver_accessibility_routes",__name__)

def _no_store(r):
    r.headers["Cache-Control"]="no-store, private"; r.headers["X-Content-Type-Options"]="nosniff"; return r
def _error(code,status): return _no_store(make_response(jsonify(error={"code":code}),status))
def _body():
    value=request.get_json(silent=True)
    if not isinstance(value,dict): raise TypeError("json_object_required")
    return value
def _translate(exc):
    if isinstance(exc,PermissionError): return _error(str(exc) or "ride_accessibility_denied",403)
    if isinstance(exc,(TypeError,ValueError)): return _error(str(exc) or "invalid_ride_accessibility_request",400)
    return _error("ride_accessibility_unavailable",503)

@bp.post("/transport/ride/driver/accessibility")
@web_security.login_required(api=True)
def set_driver_accessibility():
    identity=web_security.authenticated_identity()
    if not web_security.csrf_valid(request): return _error("csrf_failed",403)
    if not web_security.PUBLIC_WRITE_LIMITER.allow(identity): return _error("rate_limited",429)
    try:
        result=oap_ride_driver_accessibility.set_capabilities(
            driver_identity_id=identity,capabilities=_body()
        )
        return _no_store(make_response(jsonify(result),200))
    except Exception as exc: return _translate(exc)
