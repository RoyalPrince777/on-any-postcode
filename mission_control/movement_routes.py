"""Public Movement surface and authenticated private Movement APIs."""
from __future__ import annotations

from flask import Blueprint, jsonify, make_response, render_template, request

from . import (
    location_intelligence,
    movement,
    movement_match_safety,
    movement_operations,
    movement_proof,
    movement_workspace,
    routing,
    web_security,
)

bp = Blueprint("movement", __name__)


def _no_store(response):
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


def _error(code: str, message: str, status_code: int):
    return _no_store(
        make_response(jsonify(error={"code": code, "message": message}), status_code)
    )


def _body() -> dict:
    value = request.get_json(silent=True)
    if not isinstance(value, dict):
        raise TypeError("json_object_required")
    return value


def _private_identity() -> str:
    return web_security.authenticated_identity()


def _write_guard(identity_id: str):
    if not web_security.csrf_valid(request):
        return _error("csrf_failed", "Request verification failed.", 403)
    if not web_security.PUBLIC_WRITE_LIMITER.allow(identity_id):
        return _error("rate_limited", "Too many Movement requests.", 429)
    return None


def _resolved_place(
    body: dict,
    *,
    value_key: str,
    query_key: str,
    name: str,
    required: bool = True,
):
    """Resolve explicit coordinates or a user-entered postcode/place into a private place."""

    raw = body.get(value_key)
    if raw is not None:
        return movement_operations.normalize_place(raw, name=name)
    query = " ".join(str(body.get(query_key) or "").strip().split())[:120]
    if not query:
        if required:
            raise ValueError(f"{name}_required")
        return None
    resolved = location_intelligence.lookup(query)
    label = str(resolved.get("postcode") or resolved.get("query") or query)[:160]
    zone = str(
        resolved.get("postcode")
        or resolved.get("borough")
        or resolved.get("county")
        or ""
    )[:40]
    return movement_operations.normalize_place(
        {
            "label": label,
            "zone": zone,
            "latitude": resolved.get("latitude"),
            "longitude": resolved.get("longitude"),
        },
        name=name,
    )


def _operation_error(exc: Exception):
    if isinstance(exc, routing.RoutingUnavailable):
        return _error(str(exc), "Routing is not available for this request.", 503)
    if isinstance(exc, location_intelligence.LocationUnavailable):
        return _error(
            "location_lookup_unavailable",
            "Location lookup is temporarily unavailable.",
            503,
        )
    if isinstance(exc, movement_workspace.MovementWorkspaceUnavailable):
        return _error(
            "movement_workspace_unavailable",
            "Movement workspace is temporarily unavailable.",
            503,
        )
    if isinstance(exc, PermissionError):
        code = str(exc) or "movement_access_denied"
        status_code = 404 if code in {"booking_not_found"} else 403
        return _error(code, "Movement access is not available for this request.", status_code)
    if isinstance(exc, (TypeError, ValueError)):
        return _error(str(exc) or "invalid_movement_request", "Invalid Movement request.", 400)
    return _error("movement_unavailable", "Movement is temporarily unavailable.", 503)


@bp.get("/movement")
def movement_home():
    """Render Movement architecture without dispatch or carrier operations."""

    response = make_response(
        render_template(
            "movement.html",
            movement=movement.get_public_movement(),
            movement_proof=movement_proof.status(),
            sample_route=movement_proof.route_proof(
                request.args.get("from") or "Mitcham",
                request.args.get("to") or "London Bridge",
                request.args.get("profile") or "driving",
            ),
        )
    )
    return _no_store(response)


@bp.get("/movement/status")
def movement_status():
    """Expose only coarse readiness without private booking/device data."""

    status = movement.get_public_movement_status()
    status["proof"] = movement_proof.status()
    return _no_store(make_response(jsonify(status)))


@bp.get("/movement/route-proof")
def public_route_proof():
    """Return a public-safe Movement estimate from explicit area names only."""

    return _no_store(
        make_response(
            jsonify(
                movement_proof.route_proof(
                    request.args.get("from") or request.args.get("origin") or "Mitcham",
                    request.args.get("to") or request.args.get("destination") or "London Bridge",
                    request.args.get("profile") or "driving",
                )
            )
        )
    )


@bp.get("/movement/request-preview")
def movement_request_preview():
    """Preview a request receipt without storing, charging or dispatching."""

    receipt = movement_proof.request_receipt(
        {
            "origin": request.args.get("from") or request.args.get("origin") or "Mitcham",
            "destination": request.args.get("to") or request.args.get("destination") or "London Bridge",
            "purpose": request.args.get("purpose") or "movement_request",
            "profile": request.args.get("profile") or "driving",
        }
    )
    return _no_store(make_response(jsonify(receipt)))


@bp.get("/mission/war-room/movement/proof")
@bp.get("/mission/movement/proof")
@web_security.login_required(api=True, founder_only=True)
def founder_movement_proof():
    """Return the private-safe Movement proof status for War Room."""

    return _no_store(make_response(jsonify(movement_proof.status())))


@bp.get("/movement/workspace")
@web_security.login_required()
def movement_workspace_home():
    """Render only the authenticated person's Movement bookings/work state."""

    identity = _private_identity()
    try:
        private_snapshot = movement_workspace.snapshot(identity)
        response = make_response(
            render_template(
                "movement_workspace.html",
                snapshot=private_snapshot,
                routing_status=routing.status(),
            )
        )
        return _no_store(response)
    except Exception as exc:  # noqa: BLE001 - keep DB/provider details private.
        return _operation_error(exc)


@bp.post("/movement/route")
@web_security.login_required(api=True)
def route_plan():
    """Calculate a private ETA/distance snapshot; never dispatch or expose geometry."""

    identity = _private_identity()
    if guard := _write_guard(identity):
        return guard
    try:
        body = _body()
        pickup = _resolved_place(
            body,
            value_key="pickup",
            query_key="pickup_query",
            name="pickup",
        )
        destination = _resolved_place(
            body,
            value_key="destination",
            query_key="destination_query",
            name="destination",
        )
        result = routing.route(
            pickup_latitude=pickup["latitude"],
            pickup_longitude=pickup["longitude"],
            destination_latitude=destination["latitude"],
            destination_longitude=destination["longitude"],
            profile=body.get("profile", "driving"),
        )
        return _no_store(make_response(jsonify(route=result), 200))
    except Exception as exc:  # noqa: BLE001 - translate to redacted API errors.
        return _operation_error(exc)


@bp.post("/movement/bookings")
@web_security.login_required(api=True)
def create_booking():
    """Persist an authenticated booking request without dispatch or payment."""

    identity = _private_identity()
    if guard := _write_guard(identity):
        return guard
    try:
        body = _body()
        pickup = _resolved_place(
            body,
            value_key="pickup",
            query_key="pickup_query",
            name="pickup",
        )
        destination = _resolved_place(
            body,
            value_key="destination",
            query_key="destination_query",
            name="destination",
            required=False,
        )
        service = str(body.get("service_type") or "").strip().casefold()
        route_snapshot = None
        if (
            destination is not None
            and service in {"ride", "delivery"}
            and routing.production_ready()
        ):
            route_snapshot = routing.route(
                pickup_latitude=pickup["latitude"],
                pickup_longitude=pickup["longitude"],
                destination_latitude=destination["latitude"],
                destination_longitude=destination["longitude"],
                profile="driving",
            )
        key = request.headers.get("Idempotency-Key") or body.get("idempotency_key")
        result = movement_operations.STORE.create_booking(
            member_identity_id=identity,
            service_type=service,
            pickup=pickup,
            destination=destination,
            scheduled_for=body.get("scheduled_for"),
            route_snapshot=route_snapshot,
            idempotency_key=key,
        )
        return _no_store(make_response(jsonify(booking=result), 201))
    except Exception as exc:  # noqa: BLE001
        return _operation_error(exc)


@bp.get("/movement/bookings/<booking_id>")
@web_security.login_required(api=True)
def get_booking(booking_id: str):
    """Read one booking only for its authenticated member owner."""

    identity = _private_identity()
    try:
        result = movement_operations.STORE.get_booking(
            booking_id=booking_id, identity_id=identity
        )
        if result is None:
            return _error("booking_not_found", "Booking not found.", 404)
        return _no_store(make_response(jsonify(booking=result), 200))
    except Exception as exc:  # noqa: BLE001
        return _operation_error(exc)


@bp.post("/movement/availability")
@web_security.login_required(api=True)
def set_availability():
    """Set coarse availability for an already-certified driver/rider/courier."""

    identity = _private_identity()
    if guard := _write_guard(identity):
        return guard
    try:
        body = _body()
        result = movement_operations.STORE.set_availability(
            identity_id=identity,
            role_type=body.get("role_type"),
            state=body.get("state"),
            zone=body.get("zone", ""),
            available_until=body.get("available_until"),
        )
        return _no_store(make_response(jsonify(availability=result), 200))
    except Exception as exc:  # noqa: BLE001
        return _operation_error(exc)


@bp.post("/movement/bookings/<booking_id>/match")
@web_security.login_required(api=True)
def propose_match(booking_id: str):
    """Create a deterministic match proposal; this does not dispatch anyone."""

    identity = _private_identity()
    if guard := _write_guard(identity):
        return guard
    try:
        result = movement_match_safety.STORE.propose_match(
            booking_id=booking_id,
            member_identity_id=identity,
        )
        if result is None:
            return _no_store(
                make_response(
                    jsonify(match=None, status="no_eligible_candidate_available"),
                    200,
                )
            )
        return _no_store(make_response(jsonify(match=result), 201))
    except Exception as exc:  # noqa: BLE001
        return _operation_error(exc)


@bp.post("/movement/matches/<proposal_id>/accept")
@web_security.login_required(api=True)
def accept_match(proposal_id: str):
    """Allow the proposed human worker to accept; external dispatch stays off."""

    identity = _private_identity()
    if guard := _write_guard(identity):
        return guard
    try:
        result = movement_match_safety.STORE.accept_match(
            proposal_id=proposal_id,
            worker_identity_id=identity,
        )
        return _no_store(make_response(jsonify(match=result), 200))
    except Exception as exc:  # noqa: BLE001
        return _operation_error(exc)


@bp.post("/movement/bookings/<booking_id>/tracking/consent")
@web_security.login_required(api=True)
def grant_tracking_consent(booking_id: str):
    """Opt in to sharing only the caller's own live location for one booking."""

    identity = _private_identity()
    if guard := _write_guard(identity):
        return guard
    try:
        body = _body()
        result = movement_operations.STORE.grant_tracking_consent(
            booking_id=booking_id,
            identity_id=identity,
            expires_at=body.get("expires_at"),
        )
        return _no_store(make_response(jsonify(consent=result), 200))
    except Exception as exc:  # noqa: BLE001
        return _operation_error(exc)


@bp.delete("/movement/bookings/<booking_id>/tracking/consent")
@web_security.login_required(api=True)
def revoke_tracking_consent(booking_id: str):
    """Immediately revoke the caller's own tracking consent."""

    identity = _private_identity()
    if guard := _write_guard(identity):
        return guard
    try:
        revoked = movement_operations.STORE.revoke_tracking_consent(
            booking_id=booking_id,
            identity_id=identity,
        )
        return _no_store(make_response(jsonify(revoked=revoked), 200))
    except Exception as exc:  # noqa: BLE001
        return _operation_error(exc)


@bp.post("/movement/bookings/<booking_id>/tracking/points")
@web_security.login_required(api=True)
def record_tracking_point(booking_id: str):
    """Store an expiring private point only while explicit consent is active."""

    identity = _private_identity()
    if guard := _write_guard(identity):
        return guard
    try:
        body = _body()
        result = movement_operations.STORE.record_tracking_point(
            booking_id=booking_id,
            identity_id=identity,
            latitude=body.get("latitude"),
            longitude=body.get("longitude"),
        )
        return _no_store(make_response(jsonify(point=result), 201))
    except Exception as exc:  # noqa: BLE001
        return _operation_error(exc)


@bp.post("/movement/esim/requests")
@web_security.login_required(api=True)
def request_esim_connectivity():
    """Record a connectivity request; never activate/install/switch a profile."""

    identity = _private_identity()
    if guard := _write_guard(identity):
        return guard
    try:
        body = _body()
        result = movement_operations.STORE.request_esim_connectivity(
            identity_id=identity,
            purpose=body.get("purpose"),
            booking_id=body.get("booking_id"),
        )
        return _no_store(make_response(jsonify(esim_request=result), 201))
    except Exception as exc:  # noqa: BLE001
        return _operation_error(exc)


@bp.post("/movement/bookings/<booking_id>/payment-intents")
@web_security.login_required(api=True)
def create_payment_intent(booking_id: str):
    """Record a provider-required payment intent; never authorize/capture money."""

    identity = _private_identity()
    if guard := _write_guard(identity):
        return guard
    try:
        body = _body()
        key = request.headers.get("Idempotency-Key") or body.get("idempotency_key")
        result = movement_operations.STORE.create_payment_intent(
            booking_id=booking_id,
            member_identity_id=identity,
            amount_minor=body.get("amount_minor"),
            currency=body.get("currency", "GBP"),
            idempotency_key=key,
        )
        return _no_store(make_response(jsonify(payment_intent=result), 201))
    except Exception as exc:  # noqa: BLE001
        return _operation_error(exc)


@bp.post("/movement/bookings/<booking_id>/link-up")
@web_security.login_required(api=True)
def ensure_trip_channel(booking_id: str):
    """Create only a trip-to-Link-Up binding; Link Up owns message bodies."""

    identity = _private_identity()
    if guard := _write_guard(identity):
        return guard
    try:
        result = movement_operations.STORE.ensure_trip_channel(
            booking_id=booking_id,
            identity_id=identity,
        )
        return _no_store(make_response(jsonify(channel=result), 201))
    except Exception as exc:  # noqa: BLE001
        return _operation_error(exc)
