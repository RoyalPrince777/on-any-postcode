"""Authenticated Link delivery-state and short-lived typing APIs."""
from __future__ import annotations

from flask import Blueprint, jsonify, make_response, request

from . import link_activity, product_store, public_store, web_security

bp = Blueprint("link_message_state", __name__)

MESSAGE_ERRORS = (
    TypeError,
    ValueError,
    product_store.ProductStoreUnavailable,
    public_store.PublicStoreUnavailable,
    link_activity.LinkActivityUnavailable,
)


def _no_store(response):
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


def _error(code: str, status_code: int):
    return _no_store(make_response(jsonify(error={"code": code}), status_code))


def _identity_user() -> tuple[str, dict]:
    user = web_security.current_authenticated_user()
    return str(user["id"]), user


def _mutation_guard(identity: str):
    if not web_security.csrf_valid(request):
        return _error("csrf_failed", 403)
    if not web_security.PUBLIC_WRITE_LIMITER.allow(identity):
        return _error("rate_limited", 429)
    return None


def _failure(exc: Exception):
    code = str(exc) or "linkup_unavailable"
    if isinstance(exc, (TypeError, ValueError)):
        if code in {"link_blocked", "accepted_link_required"}:
            return _error(code, 403)
        if code in {"linkup_rate_limit", "rate_limited"}:
            return _error(code, 429)
        return _error(code, 400)
    return _error("linkup_unavailable", 503)


@bp.get("/linkup/messages/status")
@web_security.login_required(api=True)
def status():
    store = product_store.status()
    activity = link_activity.status()
    return _no_store(
        make_response(
            jsonify(
                ready=bool(store.get("tables", {}).get("messages")),
                landed_semantics="persisted_oap_data",
                seen_semantics="recipient_read_receipt",
                retry_client_side=True,
                first_party=True,
                activity_ready=bool(activity.get("ready")),
                typing_ttl_seconds=activity.get("typing_ttl_seconds"),
                typing_stores_content=False,
            )
        )
    )


@bp.post("/linkup/messages")
@web_security.login_required(api=True)
def send_message():
    identity, user = _identity_user()
    if guarded := _mutation_guard(identity):
        return guarded
    try:
        public_store.ensure_authenticated_user(
            identity,
            email=str(user["email"]),
            display_name=str(user["name"]),
        )
        payload = request.get_json(silent=True) or request.form
        message_id = product_store.send_message(
            identity,
            payload.get("recipient_id"),
            payload.get("body"),
        )
        return _no_store(
            make_response(
                jsonify(message_id=message_id, state="landed"),
                201,
            )
        )
    except MESSAGE_ERRORS as exc:
        return _failure(exc)


@bp.get("/linkup/messages/state")
@web_security.login_required(api=True)
def message_state():
    identity, _user = _identity_user()
    try:
        states = product_store.message_states(identity, request.args.get("peer_id", ""))
        return _no_store(make_response(jsonify(messages=states)))
    except MESSAGE_ERRORS as exc:
        return _failure(exc)


@bp.post("/linkup/messages/<message_id>/seen")
@web_security.login_required(api=True)
def seen(message_id: str):
    identity, _user = _identity_user()
    if guarded := _mutation_guard(identity):
        return guarded
    try:
        if not product_store.mark_message_read(identity, message_id):
            return _error("message_not_found", 404)
        return _no_store(make_response(jsonify(message_id=message_id, state="seen")))
    except MESSAGE_ERRORS as exc:
        return _failure(exc)


@bp.get("/linkup/activity/typing")
@web_security.login_required(api=True)
def typing_state():
    identity, _user = _identity_user()
    try:
        active = link_activity.peer_typing(identity, request.args.get("peer_id", ""))
        return _no_store(make_response(jsonify(typing=active)))
    except MESSAGE_ERRORS as exc:
        return _failure(exc)


@bp.post("/linkup/activity/typing")
@web_security.login_required(api=True)
def typing_update():
    identity, _user = _identity_user()
    if guarded := _mutation_guard(identity):
        return guarded
    try:
        payload = request.get_json(silent=True) or request.form
        raw_active = payload.get("active")
        if isinstance(raw_active, bool):
            active = raw_active
        else:
            normalized = str(raw_active or "").strip().casefold()
            if normalized not in {"true", "false", "1", "0"}:
                raise ValueError("invalid_typing_state")
            active = normalized in {"true", "1"}
        current = link_activity.set_typing(
            identity,
            payload.get("peer_id"),
            active=active,
        )
        return _no_store(make_response(jsonify(typing=current)))
    except MESSAGE_ERRORS as exc:
        return _failure(exc)
