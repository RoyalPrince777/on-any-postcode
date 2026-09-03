"""Protected OAP Link Around Now and Live Spot routes."""
from __future__ import annotations

import uuid

from flask import Blueprint, jsonify, make_response, request

from . import (
    link_presence,
    link_relationships,
    linkup_safety,
    postgres_db,
    web_security,
)

bp = Blueprint("link_presence", __name__)


def _no_store(response):
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


def _error(code: str, status_code: int):
    return _no_store(make_response(jsonify(error={"code": code}), status_code))


def _identity() -> str:
    return web_security.authenticated_identity()


def _payload() -> dict[str, object]:
    data = request.get_json(silent=True) or {}
    if not isinstance(data, dict):
        raise TypeError("invalid_request")
    return data


def _mutation_guard():
    if not web_security.csrf_valid(request):
        return _error("csrf_failed", 403)
    return None


def _value_error(exc: TypeError | ValueError):
    code = str(exc)
    if code in {"link_blocked", "accepted_link_required", "live_spot_visibility_required"}:
        return _error(code, 403)
    return _error(code or "invalid_request", 400)


def _visibility_state(owner_id: str, peer_id: str) -> dict[str, bool]:
    try:
        owner = str(uuid.UUID(owner_id))
        peer = str(uuid.UUID(peer_id))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError("invalid_peer") from exc
    if owner == peer:
        raise ValueError("cannot_share_with_self")
    try:
        if linkup_safety.blocked_between(owner, peer):
            raise ValueError("link_blocked")
        if not link_relationships.accepted_between(owner, peer):
            raise ValueError("accepted_link_required")
        with postgres_db.connect(readonly=True) as connection:
            row = connection.execute(
                """SELECT around_now,live_spot FROM link_presence_visibility
                   WHERE owner_id=%s AND viewer_id=%s LIMIT 1""",
                (owner, peer),
            ).fetchone()
    except ValueError:
        raise
    except Exception as exc:  # noqa: BLE001 - privacy state must fail closed across DB/guard failures.
        raise link_presence.LinkPresenceUnavailable("presence_visibility_read_failed") from exc
    if row is None:
        return {"around_now": False, "live_spot": False}
    return {"around_now": bool(row[0]), "live_spot": bool(row[1])}


@bp.get("/linkup/presence/status")
@web_security.login_required(api=True)
def status():
    return _no_store(make_response(jsonify(link_presence.status())))


@bp.get("/linkup/presence/visibility/<peer_id>")
@web_security.login_required(api=True)
def visibility_state(peer_id: str):
    try:
        return _no_store(make_response(jsonify(_visibility_state(_identity(), peer_id))))
    except (TypeError, ValueError) as exc:
        return _value_error(exc)
    except link_presence.LinkPresenceUnavailable:
        return _error("link_presence_unavailable", 503)


@bp.post("/linkup/presence/visibility")
@web_security.login_required(api=True)
def visibility():
    guarded = _mutation_guard()
    if guarded is not None:
        return guarded
    try:
        data = _payload()
        result = link_presence.set_visibility(
            _identity(),
            data.get("peer_id"),
            around_now=data.get("around_now", False),
            live_spot=data.get("live_spot", False),
        )
        return _no_store(make_response(jsonify(result)))
    except (TypeError, ValueError) as exc:
        return _value_error(exc)
    except link_presence.LinkPresenceUnavailable:
        return _error("link_presence_unavailable", 503)


@bp.post("/linkup/presence/heartbeat")
@web_security.login_required(api=True)
def heartbeat():
    guarded = _mutation_guard()
    if guarded is not None:
        return guarded
    try:
        data = _payload()
        result = link_presence.heartbeat(
            _identity(), around_now=data.get("around_now", False)
        )
        return _no_store(make_response(jsonify(result)))
    except (TypeError, ValueError) as exc:
        return _value_error(exc)
    except link_presence.LinkPresenceUnavailable:
        return _error("link_presence_unavailable", 503)


@bp.get("/linkup/presence/<peer_id>")
@web_security.login_required(api=True)
def peer_presence(peer_id: str):
    try:
        return _no_store(
            make_response(
                jsonify(
                    peer_id=peer_id,
                    around_now=link_presence.around_now(_identity(), peer_id),
                )
            )
        )
    except (TypeError, ValueError) as exc:
        return _value_error(exc)
    except link_presence.LinkPresenceUnavailable:
        return _error("link_presence_unavailable", 503)


@bp.post("/linkup/live-spot")
@web_security.login_required(api=True)
def live_spot_start():
    guarded = _mutation_guard()
    if guarded is not None:
        return guarded
    try:
        data = _payload()
        result = link_presence.start_live_spot(
            _identity(),
            data.get("peer_id"),
            latitude=data.get("latitude"),
            longitude=data.get("longitude"),
            accuracy_m=data.get("accuracy_m"),
            duration_minutes=data.get("duration_minutes", 15),
        )
        return _no_store(make_response(jsonify(result)))
    except (TypeError, ValueError) as exc:
        return _value_error(exc)
    except link_presence.LinkPresenceUnavailable:
        return _error("live_spot_unavailable", 503)


@bp.get("/linkup/live-spot/<peer_id>")
@web_security.login_required(api=True)
def live_spot_read(peer_id: str):
    try:
        spot = link_presence.read_live_spot(_identity(), peer_id)
        if spot is None:
            return _error("live_spot_not_active", 404)
        return _no_store(make_response(jsonify(peer_id=peer_id, **spot)))
    except (TypeError, ValueError) as exc:
        return _value_error(exc)
    except link_presence.LinkPresenceUnavailable:
        return _error("live_spot_unavailable", 503)


@bp.delete("/linkup/live-spot/<peer_id>")
@web_security.login_required(api=True)
def live_spot_stop(peer_id: str):
    guarded = _mutation_guard()
    if guarded is not None:
        return guarded
    try:
        stopped = link_presence.stop_live_spot(_identity(), peer_id)
        return _no_store(make_response(jsonify(stopped=stopped)))
    except (TypeError, ValueError) as exc:
        return _value_error(exc)
    except link_presence.LinkPresenceUnavailable:
        return _error("live_spot_unavailable", 503)
