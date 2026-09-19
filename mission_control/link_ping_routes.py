"""Authenticated Ping Up routes for Link Up."""
from __future__ import annotations

from flask import Blueprint, jsonify, make_response, request

from . import link_ping, web_security

bp = Blueprint("link_ping", __name__)

def _no_store(response):
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response

def _error(code: str, status_code: int):
    return _no_store(make_response(jsonify(error={"code": code}), status_code))

def _identity() -> str:
    return web_security.authenticated_identity()

def _guard(identity: str):
    if not web_security.csrf_valid(request):
        return _error("csrf_failed", 403)
    if not web_security.PUBLIC_WRITE_LIMITER.allow(identity):
        return _error("rate_limited", 429)
    return None

def _failure(exc: Exception):
    code = str(exc) or "ping_unavailable"
    if isinstance(exc, (TypeError, ValueError)):
        if code in {"link_blocked", "accepted_link_required", "ping_muted"}:
            return _error(code, 403)
        if code in {"ping_rate_limited", "rate_limited"}:
            return _error(code, 429)
        return _error(code, 400)
    return _error("ping_unavailable", 503)

@bp.get("/linkup/ping/status")
@web_security.login_required(api=True)
def status():
    return _no_store(make_response(jsonify(link_ping.status()), 200))

@bp.post("/linkup/ping")
@web_security.login_required(api=True)
def send_ping():
    identity = _identity()
    if guarded := _guard(identity):
        return guarded
    try:
        payload = request.get_json(silent=True) or request.form
        result = link_ping.send(
            identity,
            payload.get("recipient_id"),
            intensity=payload.get("intensity", "normal"),
        )
        return _no_store(make_response(jsonify(result), 201))
    except Exception as exc:  # noqa: BLE001
        return _failure(exc)

@bp.get("/linkup/ping/incoming")
@web_security.login_required(api=True)
def incoming():
    try:
        return _no_store(make_response(jsonify(pings=link_ping.incoming(_identity())), 200))
    except Exception as exc:  # noqa: BLE001
        return _failure(exc)

@bp.post("/linkup/ping/<ping_id>/seen")
@web_security.login_required(api=True)
def seen(ping_id: str):
    identity = _identity()
    if guarded := _guard(identity):
        return guarded
    try:
        if not link_ping.mark_seen(identity, ping_id):
            return _error("ping_not_found", 404)
        return _no_store(make_response(jsonify(ping_id=ping_id, state="seen"), 200))
    except Exception as exc:  # noqa: BLE001
        return _failure(exc)

@bp.post("/linkup/ping/mute")
@web_security.login_required(api=True)
def mute():
    identity = _identity()
    if guarded := _guard(identity):
        return guarded
    try:
        payload = request.get_json(silent=True) or request.form
        raw = payload.get("muted")
        muted = raw if isinstance(raw, bool) else str(raw or "").strip().casefold() in {"1","true","yes","on"}
        result = link_ping.set_mute(identity, payload.get("peer_id"), muted=muted)
        return _no_store(make_response(jsonify(muted=result), 200))
    except Exception as exc:  # noqa: BLE001
        return _failure(exc)
