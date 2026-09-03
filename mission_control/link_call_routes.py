"""Authenticated, fail-closed Call and Face Up session routes."""
from __future__ import annotations

from flask import Blueprint, jsonify, make_response, request

from . import link_call_audit, web_security

bp = Blueprint("link_call_audit", __name__)


def _no_store(response):
    response.headers["Cache-Control"] = "no-store"
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
        code = str(exc) or "invalid_call_request"
        if code in {"accepted_link_required", "link_blocked"}:
            return _error(code, 403)
        if code == "active_call_exists":
            return _error(code, 409)
        return _error(code, 400)
    if isinstance(exc, link_call_audit.LinkCallAuditUnavailable):
        return _error("link_call_unavailable", 503)
    return _error("link_call_unavailable", 503)


@bp.get("/linkup/calls/status")
@web_security.login_required(api=True)
def call_status():
    state = link_call_audit.status()
    return _no_store(
        make_response(
            jsonify(
                ready=bool(state.get("ready")),
                schema_ready=bool(state.get("schema_ready")),
                retention_configured=bool(state.get("retention_configured")),
                records_media=False,
            ),
            200,
        )
    )


@bp.get("/linkup/calls/active")
@web_security.login_required(api=True)
def active_calls():
    try:
        sessions = link_call_audit.list_active(_identity())
        return _no_store(make_response(jsonify(sessions=sessions), 200))
    except Exception as exc:  # noqa: BLE001
        return _failure(exc)


@bp.post("/linkup/calls")
@web_security.login_required(api=True)
def start_call():
    if guard := _csrf_guard():
        return guard
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return _error("json_body_required", 415)
    try:
        session_id = link_call_audit.start_session(
            _identity(),
            payload.get("recipient_id"),
            mode=payload.get("mode"),
        )
        return _no_store(make_response(jsonify(session_id=session_id), 201))
    except Exception as exc:  # noqa: BLE001
        return _failure(exc)


@bp.post("/linkup/calls/<session_id>/answer")
@web_security.login_required(api=True)
def answer_call(session_id: str):
    if guard := _csrf_guard():
        return guard
    try:
        answered = link_call_audit.answer_session(_identity(), session_id)
        if not answered:
            return _error("call_session_not_found", 404)
        return _no_store(make_response(jsonify(answered=True), 200))
    except Exception as exc:  # noqa: BLE001
        return _failure(exc)


@bp.post("/linkup/calls/<session_id>/finish")
@web_security.login_required(api=True)
def finish_call(session_id: str):
    if guard := _csrf_guard():
        return guard
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return _error("json_body_required", 415)
    try:
        finished = link_call_audit.finish_session(
            _identity(), session_id, outcome=payload.get("outcome")
        )
        if not finished:
            return _error("call_session_not_found", 404)
        return _no_store(make_response(jsonify(finished=True), 200))
    except Exception as exc:  # noqa: BLE001
        return _failure(exc)
