# ruff: noqa: I001
"""Authenticated OAP Ride earnings APIs."""
from __future__ import annotations
from flask import Blueprint, jsonify, make_response
from . import oap_ride_earnings, web_security

bp=Blueprint("oap_ride_earnings_routes",__name__)

@bp.get("/transport/ride/driver/earnings")
@web_security.login_required(api=True)
def driver_earnings():
    identity=web_security.authenticated_identity()
    payload=oap_ride_earnings.driver_summary(driver_identity_id=identity)
    response=make_response(jsonify(payload),200)
    response.headers["Cache-Control"]="no-store, private"
    response.headers["X-Content-Type-Options"]="nosniff"
    return response
