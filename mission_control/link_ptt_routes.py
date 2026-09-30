"""Authenticated private PTT floor control; no server-side media-intercept claim."""
from __future__ import annotations

from flask import Blueprint, jsonify, make_response, request

from . import link_ptt_floor, web_security

bp = Blueprint("link_ptt_floor", __name__)


def _reply(payload: dict, code: int = 200):
    result = make_response(jsonify(**payload), code)
    result.headers["Cache-Control"] = "no-store"
    result.headers["X-Content-Type-Options"] = "nosniff"
    return result


def _failure(exc: Exception):
    if isinstance(exc, ValueError):
        code = str(exc)
        if code in {"accepted_link_required", "link_blocked", "active_ptt_call_required"}:
            return _reply({"error": {"code": code}}, 403)
        if code in {"ptt_floor_busy", "ptt_floor_not_holder"}:
            return _reply({"error": {"code": code}}, 409)
        return _reply({"error": {"code": code}}, 400)
    return _reply({"error": {"code": "ptt_floor_unavailable"}}, 503)


@bp.get("/linkup/ptt/status")
@web_security.login_required(api=True)
def ptt_status():
    return _reply(link_ptt_floor.status())


@bp.get("/linkup/calls/<session_id>/ptt/floor")
@web_security.login_required(api=True)
def floor_status(session_id: str):
    try:
        return _reply(link_ptt_floor.read(web_security.authenticated_identity(), session_id))
    except Exception as exc:  # noqa: BLE001 - fail-closed API response.
        return _failure(exc)


@bp.post("/linkup/calls/<session_id>/ptt/floor")
@web_security.login_required(api=True)
def mutate_floor(session_id: str):
    if not web_security.csrf_valid(request):
        return _reply({"error": {"code": "csrf_failed"}}, 403)
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return _reply({"error": {"code": "json_body_required"}}, 415)
    try:
        result = link_ptt_floor.floor(
            web_security.authenticated_identity(),
            session_id,
            action=payload.get("action"),
        )
        return _reply(result)
    except Exception as exc:  # noqa: BLE001 - no details from storage/guards.
        return _failure(exc)
