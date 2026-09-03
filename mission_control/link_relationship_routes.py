"""Authenticated OAP Link Request and Purpose Link routes."""
from __future__ import annotations

from flask import Blueprint, jsonify, make_response, redirect, request

from . import link_relationships, web_security

bp = Blueprint("link_relationships", __name__)


def _no_store(response):
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


def _error(code: str, status: int):
    return _no_store(make_response(jsonify(error={"code": code}), status))


def _identity() -> str:
    return web_security.authenticated_identity()


def _guard(identity: str):
    if not web_security.csrf_valid(request):
        return _error("csrf_failed", 403)
    if not web_security.PUBLIC_WRITE_LIMITER.allow(identity):
        return _error("rate_limited", 429)
    return None


def _failure(exc: Exception):
    if isinstance(exc, (TypeError, ValueError)):
        return _error(str(exc) or "invalid_link_request", 400)
    if isinstance(exc, link_relationships.LinkRelationshipsUnavailable):
        return _error("link_relationships_unavailable", 503)
    return _error("link_relationships_unavailable", 503)


def _back_to_linkup():
    return _no_store(make_response(redirect("/linkup")))


@bp.get("/linkup/relationships/status")
@web_security.login_required(api=True)
def relationship_status():
    status = link_relationships.status()
    return _no_store(make_response(jsonify(ready=bool(status.get("ready"))), 200))


@bp.get("/linkup/relationships")
@web_security.login_required(api=True)
def list_relationships():
    try:
        links = link_relationships.list_for_identity(_identity())
        return _no_store(make_response(jsonify(links=links), 200))
    except Exception as exc:  # noqa: BLE001
        return _failure(exc)


@bp.post("/linkup/requests")
@web_security.login_required(api=True)
def create_request():
    identity = _identity()
    if guard := _guard(identity):
        return guard
    try:
        payload = request.get_json(silent=True) if request.is_json else request.form
        relationship_id = link_relationships.request_link(
            identity,
            payload.get("recipient_id"),
            link_kind=payload.get("link_kind", "permanent"),
            purpose_text=payload.get("purpose_text", ""),
            expires_at=payload.get("expires_at"),
        )
        if request.is_json:
            return _no_store(make_response(jsonify(relationship_id=relationship_id, status="pending"), 201))
        return _back_to_linkup()
    except Exception as exc:  # noqa: BLE001
        return _failure(exc)


@bp.post("/linkup/requests/<relationship_id>/respond")
@web_security.login_required(api=True)
def respond_request(relationship_id: str):
    identity = _identity()
    if guard := _guard(identity):
        return guard
    try:
        decision = request.get_json(silent=True).get("decision") if request.is_json and isinstance(request.get_json(silent=True), dict) else request.form.get("decision")
        changed = link_relationships.respond(identity, relationship_id, decision)
        if not changed:
            return _error("link_request_not_found", 404)
        if request.is_json:
            return _no_store(make_response(jsonify(updated=True, status=decision), 200))
        return _back_to_linkup()
    except Exception as exc:  # noqa: BLE001
        return _failure(exc)


@bp.post("/linkup/relationships/<relationship_id>/revoke")
@web_security.login_required(api=True)
def revoke_relationship(relationship_id: str):
    identity = _identity()
    if guard := _guard(identity):
        return guard
    try:
        changed = link_relationships.revoke(identity, relationship_id)
        if not changed:
            return _error("link_relationship_not_found", 404)
        if request.is_json:
            return _no_store(make_response(jsonify(revoked=True), 200))
        return _back_to_linkup()
    except Exception as exc:  # noqa: BLE001
        return _failure(exc)
