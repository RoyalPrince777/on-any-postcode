"""Authenticated unified Incoming API for Link Up."""
from __future__ import annotations

from flask import Blueprint, jsonify, make_response

from . import link_incoming, web_security

bp = Blueprint("link_incoming", __name__)

def _no_store(response):
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response

@bp.get("/linkup/incoming/status")
@web_security.login_required(api=True)
def status():
    return _no_store(make_response(jsonify(link_incoming.status()), 200))

@bp.get("/linkup/incoming")
@web_security.login_required(api=True)
def incoming():
    try:
        events = link_incoming.list_incoming(web_security.authenticated_identity())
        return _no_store(make_response(jsonify(events=events), 200))
    except (TypeError, ValueError, link_incoming.LinkIncomingUnavailable):
        return _no_store(
            make_response(jsonify(error={"code": "incoming_unavailable"}), 503)
        )
