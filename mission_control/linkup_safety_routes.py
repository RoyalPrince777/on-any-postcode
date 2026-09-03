"""Authenticated Link Up Block/Report routes."""
from __future__ import annotations

from flask import Blueprint, jsonify, make_response, request

from . import linkup_safety, web_security

bp = Blueprint("linkup_safety", __name__)


def _no_store(response):
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


def _error(code: str, status: int):
    return _no_store(make_response(jsonify(error={"code": code}), status))


def _identity() -> str:
    return web_security.authenticated_identity()


def _body() -> dict:
    value = request.get_json(silent=True)
    if not isinstance(value, dict):
        raise TypeError("json_object_required")
    return value


def _guard(identity: str):
    if not web_security.csrf_valid(request):
        return _error("csrf_failed", 403)
    if not web_security.PUBLIC_WRITE_LIMITER.allow(identity):
        return _error("rate_limited", 429)
    return None


def _failure(exc: Exception):
    if isinstance(exc, (TypeError, ValueError)):
        return _error(str(exc) or "invalid_linkup_safety_request", 400)
    if isinstance(exc, linkup_safety.LinkUpSafetyUnavailable):
        return _error("linkup_safety_unavailable", 503)
    return _error("linkup_safety_unavailable", 503)


@bp.get("/linkup/safety/status")
@web_security.login_required(api=True)
def safety_status():
    status = linkup_safety.status()
    return _no_store(make_response(jsonify(ready=bool(status.get("ready"))), 200))


@bp.post("/linkup/blocks")
@web_security.login_required(api=True)
def create_block():
    identity = _identity()
    if guard := _guard(identity):
        return guard
    try:
        body = _body()
        linkup_safety.block(identity, body.get("member_id"))
        return _no_store(make_response(jsonify(blocked=True), 201))
    except Exception as exc:  # noqa: BLE001
        return _failure(exc)


@bp.delete("/linkup/blocks/<member_id>")
@web_security.login_required(api=True)
def delete_block(member_id: str):
    identity = _identity()
    if guard := _guard(identity):
        return guard
    try:
        removed = linkup_safety.unblock(identity, member_id)
        return _no_store(make_response(jsonify(unblocked=removed), 200))
    except Exception as exc:  # noqa: BLE001
        return _failure(exc)


@bp.post("/linkup/reports")
@web_security.login_required(api=True)
def create_report():
    identity = _identity()
    if guard := _guard(identity):
        return guard
    try:
        body = _body()
        report_id = linkup_safety.report(
            identity,
            body.get("member_id"),
            message_id=body.get("message_id"),
            reason=body.get("reason"),
            detail=body.get("detail", ""),
        )
        return _no_store(make_response(jsonify(report_id=report_id, status="open"), 201))
    except Exception as exc:  # noqa: BLE001
        return _failure(exc)
