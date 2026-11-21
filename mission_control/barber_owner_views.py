"""Private barber pricing pages; scoped to the current authenticated merchant."""
from __future__ import annotations

from flask import Blueprint, jsonify, make_response, render_template, request

from . import barber_owner_pricing, web_security

bp = Blueprint("barber_owner", __name__)


def _no_store(response):
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


def _error(code: str, message: str, status: int):
    return _no_store(make_response(
        jsonify(error={"code": code, "message": message}), status
    ))


@bp.get("/local/barbers/manage")
@web_security.login_required()
def dashboard():
    try:
        pricing = barber_owner_pricing.owner_slots(
            owner_identity_id=web_security.authenticated_identity()
        )
        unavailable = False
    except RuntimeError:
        pricing = {"slots": [], "count": 0}
        unavailable = True
    return _no_store(make_response(render_template(
        "barber_owner_pricing.html",
        pricing=pricing,
        unavailable=unavailable,
        csrf_token=web_security.csrf_token(),
    )))


@bp.get("/local/barbers/manage/api")
@web_security.login_required(api=True)
def owner_slots():
    try:
        data = barber_owner_pricing.owner_slots(
            owner_identity_id=web_security.authenticated_identity()
        )
    except RuntimeError:
        return _error("barber_supply_not_ready", "Barber supply not ready.", 503)
    return _no_store(make_response(jsonify(data)))


@bp.post("/local/barbers/manage/api/prices")
@web_security.login_required(api=True)
def update_price():
    if not web_security.csrf_valid(request):
        return _error("csrf_failed", "The secure session expired.", 403)
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return _error("invalid_json", "A JSON object is required.", 400)
    try:
        data = barber_owner_pricing.update_price(
            owner_identity_id=web_security.authenticated_identity(),
            slot_id=payload.get("slot_id"),
            amount_sika=payload.get("amount_sika"),
        )
    except PermissionError:
        return _error("barber_price_locked", "This price cannot be edited.", 403)
    except (TypeError, ValueError) as exc:
        return _error("invalid_barber_price", str(exc)[:120], 400)
    except RuntimeError:
        return _error("barber_supply_not_ready", "Barber supply not ready.", 503)
    return _no_store(make_response(jsonify(data)))
