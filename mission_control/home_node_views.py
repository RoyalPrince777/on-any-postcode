"""Authenticated machine endpoints for the OAP Home Node outbound bridge."""
from __future__ import annotations

from flask import Blueprint, jsonify, make_response, request

from . import home_node_bridge

bp = Blueprint("home_node_bridge", __name__)


def _response(payload: dict, status: int = 200):
    response = make_response(jsonify(payload), status)
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    return response


def _authorised() -> bool:
    return home_node_bridge.authorised(request.headers.get("X-OAP-Home-Node-Token"))


@bp.get("/home-node/status")
def home_node_status():
    if not _authorised():
        return _response({"error": "not_found"}, 404)
    return _response(home_node_bridge.status())


@bp.get("/home-node/jobs/next")
def home_node_next_job():
    if not _authorised():
        return _response({"error": "not_found"}, 404)
    job = home_node_bridge.claim_next()
    if job is None:
        return _response({"status": "idle"}, 204)
    return _response({"status": "job", **job})


@bp.post("/home-node/jobs/<job_id>/complete")
def home_node_complete(job_id: str):
    if not _authorised():
        return _response({"error": "not_found"}, 404)
    payload = request.get_json(silent=True) or {}
    if not isinstance(payload, dict):
        return _response({"error": "invalid_payload"}, 400)
    ok = home_node_bridge.complete(
        job_id,
        result=payload.get("result"),
        error=payload.get("error"),
    )
    if not ok:
        return _response({"error": "job_not_found_or_completed"}, 404)
    return _response({"status": "accepted", "job_id": job_id})
