"""Public OAP TV surface and truth-mode status endpoint."""
from __future__ import annotations

from flask import Blueprint, jsonify, make_response, render_template

from . import tv_core

bp = Blueprint("oap_tv", __name__)

def _no_store(response):
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response

@bp.get("/tv")
def tv_home():
    return _no_store(make_response(render_template("tv.html", tv=tv_core.status())))

@bp.get("/tv/status")
def tv_status():
    return _no_store(make_response(jsonify(tv_core.status())))
