"""Authenticated, fail-closed Link Up signalling routes."""
from __future__ import annotations

from flask import Blueprint, jsonify, make_response, request

from . import link_signalling, web_security

bp = Blueprint("link_signalling", __name__)


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
        code = str(exc) or "invalid_signalling_request"
        if code == "signalling_rate_limited":
            return _error(code, 429)
        if code in {
            "accepted_link_required",
            "active_call_session_required",
            "link_blocked",
        }:
            return _error(code, 403)
        return _error(code, 400)
    if isinstance(exc, link_signalling.LinkSignallingUnavailable):
        return _error("link_signalling_unavailable", 503)
    return _error("link_signalling_unavailable", 503)


@bp.get("/linkup/signalling/status")
@web_security.login_required(api=True)
def signalling_status():
    state = link_signalling.status()
    return _no_store(make_response(jsonify(ready=bool(state.get("ready"))), 200))


@bp.post("/linkup/signalling/events")
@web_security.login_required(api=True)
def publish_event():
    if guard := _csrf_guard():
        return guard
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return _error("json_body_required", 415)
    try:
        event_id = link_signalling.publish(
            _identity(),
            payload.get("recipient_id"),
            session_id=payload.get("session_id"),
            event_type=payload.get("event_type"),
            payload=payload.get("payload", {}),
        )
        return _no_store(make_response(jsonify(event_id=event_id), 201))
    except Exception as exc:  # noqa: BLE001
        return _failure(exc)


@bp.get("/linkup/signalling/events")
@web_security.login_required(api=True)
def list_events():
    session_id = request.args.get("session_id", "")
    if not session_id:
        return _error("signalling_session_required", 400)
    try:
        events = link_signalling.list_events(
            _identity(), session_id=session_id, limit=request.args.get("limit", 100)
        )
        return _no_store(make_response(jsonify(events=events), 200))
    except (TypeError, ValueError) as exc:
        return _failure(exc)
    except Exception as exc:  # noqa: BLE001
        return _failure(exc)


@bp.post("/linkup/signalling/events/<event_id>/ack")
@web_security.login_required(api=True)
def acknowledge_event(event_id: str):
    if guard := _csrf_guard():
        return guard
    try:
        removed = link_signalling.acknowledge(_identity(), event_id)
        if not removed:
            return _error("signalling_event_not_found", 404)
        return _no_store(make_response(jsonify(acknowledged=True), 200))
    except Exception as exc:  # noqa: BLE001
        return _failure(exc)
