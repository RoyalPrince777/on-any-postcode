"""Authenticated Link Up TURN credential routes."""
from __future__ import annotations

from flask import Blueprint, jsonify, make_response, request

from . import link_turn, web_security

bp = Blueprint("link_turn", __name__)


def _no_store(response):
    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


def _error(code: str, status: int):
    return _no_store(make_response(jsonify(error={"code": code}), status))


def _identity() -> str:
    return web_security.authenticated_identity()


def _csrf_guard():
    if not web_security.csrf_valid(request):
        return _error("csrf_failed", 403)
    return None


def _failure(exc: Exception):
    if isinstance(exc, ValueError):
        code = str(exc) or "invalid_turn_request"
        if code in {"accepted_link_required", "link_blocked"}:
            return _error(code, 403)
        return _error(code, 400)
    if isinstance(exc, link_turn.LinkTurnUnavailable):
        return _error("link_turn_unavailable", 503)
    return _error("link_turn_unavailable", 503)


@bp.get("/linkup/turn/status")
@web_security.login_required(api=True)
def turn_status():
    state = link_turn.status()
    projection = {
        "configured": bool(state.get("configured")),
        "owned": bool(state.get("owned")),
        "credential_ready": bool(state.get("credential_ready")),
        "relay_verified": bool(state.get("relay_verified")),
        "ready": bool(state.get("ready")),
    }
    return _no_store(make_response(jsonify(**projection), 200))


@bp.post("/linkup/turn/credentials")
@web_security.login_required(api=True)
def turn_credentials():
    if guard := _csrf_guard():
        return guard
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return _error("json_body_required", 415)
    try:
        credentials = link_turn.issue_credentials(
            _identity(), payload.get("recipient_id")
        )
        return _no_store(make_response(jsonify(**credentials), 200))
    except Exception as exc:  # noqa: BLE001
        return _failure(exc)
