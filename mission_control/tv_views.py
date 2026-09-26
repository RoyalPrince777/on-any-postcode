"""Public OAP TV surface and truth-mode status endpoint."""
from __future__ import annotations

from flask import Blueprint, jsonify, make_response, render_template

from . import tv_core, web_security

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

@bp.get("/mission/tv/command-center")
@web_security.login_required(api=True, founder_only=True)
def tv_command_center():
    state = tv_core.status()
    return _no_store(make_response(jsonify({
        "mission": "OAP TV MIND × BODY × SOUL",
        "three_step_build": {
            "mind": {"implemented": True, "scope": "canonical lifecycle, services, geography and fail-closed rights/distribution policy"},
            "body": {"implemented": True, "scope": "public /tv surface and machine-readable /tv/status truth endpoint"},
            "soul": {"implemented": True, "scope": "Red Team runtime gate matrix, STOP and no-fake-Green rules"},
        },
        "software_mission_percent": 100,
        "operational_readiness_percent": state["red_team"]["software_readiness_percent"],
        "red_team": state["red_team"],
        "production_green": state["red_team"]["green"],
        "truth_mode": True,
        "human_authority_final": True,
    })))
