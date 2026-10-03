"""OAP Journey Travel transport-booking API surfaces."""
from __future__ import annotations

from flask import Blueprint, jsonify, make_response, request

from . import travel_transport_booking, web_security

bp = Blueprint("travel_transport_booking", __name__)


def _no_store(response):
    response.headers["Cache-Control"] = "no-store, private"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


def _error(code: str, message: str, status_code: int):
    return _no_store(
        make_response(jsonify(error={"code": code, "message": message}), status_code)
    )


def _payload() -> dict:
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        raise TypeError("json_object_required")
    return payload


def _buyer(operation):
    if not web_security.csrf_valid(request):
        return _error("csrf_failed", "The secure session expired.", 403)
    try:
        result = operation(
            _payload(),
            buyer_identity_id=web_security.authenticated_identity(),
        )
    except PermissionError as exc:
        return _error("travel_booking_not_authorized", str(exc)[:140], 403)
    except (TypeError, ValueError) as exc:
        return _error("invalid_travel_booking", str(exc)[:140], 400)
    except RuntimeError as exc:
        return _error("travel_booking_unavailable", str(exc)[:140], 503)
    return _no_store(make_response(jsonify(result)))


@bp.get("/transport/travel/status")
def status():
    return _no_store(make_response(jsonify(travel_transport_booking.status())))


@bp.post("/transport/travel/quote")
def quote():
    try:
        result = travel_transport_booking.quote(_payload())
    except (TypeError, ValueError) as exc:
        return _error("invalid_travel_quote", str(exc)[:140], 400)
    except RuntimeError as exc:
        return _error("travel_booking_unavailable", str(exc)[:140], 503)
    return _no_store(make_response(jsonify(result)))


@bp.post("/transport/travel/hold")
@web_security.login_required(api=True)
def hold():
    return _buyer(travel_transport_booking.hold)


@bp.post("/transport/travel/reservations")
@web_security.login_required(api=True)
def reserve():
    return _buyer(travel_transport_booking.reserve)


@bp.post("/transport/travel/reservations/confirm")
@web_security.login_required(api=True, founder_only=True)
def confirm():
    if not web_security.csrf_valid(request):
        return _error("csrf_failed", "The secure session expired.", 403)
    try:
        result = travel_transport_booking.confirm(
            _payload(),
            owner_identity_id=web_security.authenticated_identity(),
        )
    except PermissionError as exc:
        return _error("travel_confirmation_not_authorized", str(exc)[:140], 403)
    except (TypeError, ValueError) as exc:
        return _error("invalid_travel_confirmation", str(exc)[:140], 400)
    except RuntimeError as exc:
        return _error("travel_booking_unavailable", str(exc)[:140], 503)
    return _no_store(make_response(jsonify(result)))


@bp.post("/transport/travel/reservations/<reservation_id>/ticket")
@web_security.login_required(api=True, founder_only=True)
def issue_ticket(reservation_id: str):
    if not web_security.csrf_valid(request):
        return _error("csrf_failed", "The secure session expired.", 403)
    try:
        payload = _payload()
        result = travel_transport_booking.issue_ticket(
            owner_identity_id=web_security.authenticated_identity(),
            reservation_id=reservation_id,
            mode=payload.get("mode"),
            issued_ticket_receipt_hash=payload.get("issued_ticket_receipt_hash"),
        )
    except PermissionError as exc:
        return _error("ticket_issuance_not_authorized", str(exc)[:140], 403)
    except (TypeError, ValueError) as exc:
        return _error("invalid_ticket_issuance", str(exc)[:140], 400)
    except RuntimeError as exc:
        return _error("ticket_issuance_unavailable", str(exc)[:140], 503)
    return _no_store(make_response(jsonify(result)))
