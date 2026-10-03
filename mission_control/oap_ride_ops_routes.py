"""Authenticated OAP Ride analytics and reconciliation-case APIs."""
from __future__ import annotations
from flask import Blueprint, jsonify, make_response
from . import oap_ride_analytics, oap_ride_reconciliation_cases, web_security

bp=Blueprint("oap_ride_ops_routes",__name__)

def _no_store(r):
    r.headers["Cache-Control"]="no-store, private"
    r.headers["X-Content-Type-Options"]="nosniff"
    return r

@bp.get("/transport/ride/analytics")
@web_security.login_required(api=True)
def analytics():
    identity=web_security.authenticated_identity()
    return _no_store(make_response(jsonify(oap_ride_analytics.summary(identity_id=identity)),200))

@bp.get("/transport/ride/reconciliation-cases")
@web_security.login_required(api=True)
def reconciliation_cases():
    identity=web_security.authenticated_identity()
    return _no_store(make_response(jsonify(oap_ride_reconciliation_cases.list_for_participant(identity_id=identity)),200))
