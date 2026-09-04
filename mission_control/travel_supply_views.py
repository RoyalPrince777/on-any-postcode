"""OAP Direct, Partner Supply and registered public ecosystem surfaces."""
from __future__ import annotations

from flask import Blueprint, jsonify, make_response, render_template, request

from . import (
    partner_supply,
    travel_marketplace,
    travel_supply_policy,
    web_security,
)
from .safe_signals_views import bp as safe_signals_bp

bp = Blueprint("travel_supply", __name__)
bp.register_blueprint(safe_signals_bp)


def _no_store(response):
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


def _error(code: str, message: str, status_code: int):
    return _no_store(
        make_response(jsonify(error={"code": code, "message": message}), status_code)
    )


def _json_payload():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        raise TypeError("json_object_required")
    return payload


def _founder_write(operation):
    if not web_security.csrf_valid(request):
        return _error("csrf_failed", "The secure session expired.", 403)
    try:
        payload = _json_payload()
        result = operation(payload)
    except PermissionError as exc:
        return _error("operation_not_authorized", str(exc)[:140], 403)
    except (TypeError, ValueError) as exc:
        return _error("invalid_supply_request", str(exc)[:140], 400)
    except RuntimeError as exc:
        return _error("supply_core_unavailable", str(exc)[:140], 503)
    return _no_store(make_response(jsonify(result)))


def _buyer_write(operation):
    if not web_security.csrf_valid(request):
        return _error("csrf_failed", "The secure session expired.", 403)
    try:
        payload = _json_payload()
        result = operation(
            payload,
            buyer_identity_id=web_security.authenticated_identity(),
        )
    except PermissionError as exc:
        return _error("booking_not_authorized", str(exc)[:140], 403)
    except (TypeError, ValueError) as exc:
        return _error("invalid_booking_request", str(exc)[:140], 400)
    except RuntimeError as exc:
        return _error("booking_runtime_unavailable", str(exc)[:140], 503)
    return _no_store(make_response(jsonify(result)))


def _hybrid_catalogue(
    *,
    category: object = None,
    country: object = None,
    limit: object = 24,
) -> dict:
    """Build the OAP-owned catalogue with Direct supply deliberately first."""

    direct = travel_marketplace.public_offers(
        category=category,
        country=country,
        limit=limit,
    )
    try:
        partner = partner_supply.public_offers(category=category, limit=limit)
    except ValueError:
        # OAP Direct supports a wider category set than current partner adapters.
        # A partner that cannot serve the requested category is simply optional.
        partner = {
            "component": "OAP Partner Supply",
            "ready": True,
            "offers": [],
            "count": 0,
            "filtered_out_for_category": True,
            "external_provider_authority": False,
        }
    policy = travel_supply_policy.public_policy()
    return {
        "component": "OAP Travel Catalogue",
        "direct": direct,
        "partner": partner,
        "direct_count": int(direct.get("count", 0)),
        "partner_count": int(partner.get("count", 0)),
        "source_order": list(travel_supply_policy.PREFERRED_SOURCE_ORDER),
        "policy": policy,
        "booking_com_required": policy["booking_com_required"],
        "partner_supply_is_replaceable": True,
        "automatic_quality_ranking_across_unmatched_offers": False,
        "external_provider_authority": False,
        "human_authority_final": True,
    }


def _operator_snapshot() -> dict:
    """Decorate the bounded Founder snapshot with non-secret operator defaults."""

    snapshot = travel_marketplace.founder_snapshot()
    suppliers = list(snapshot.get("suppliers") or [])
    certified = next(
        (
            item
            for item in suppliers
            if item.get("state") == "CERTIFIED"
            and item.get("commercial_terms_state") == "CERTIFIED"
        ),
        suppliers[0] if suppliers else None,
    )
    listings = list(snapshot.get("listings") or [])
    active_listing = next(
        (item for item in listings if item.get("state") == "ACTIVE"),
        listings[0] if listings else None,
    )
    snapshot["operator"] = {
        "supplier_ready": certified is not None,
        "owner_identity_id": certified.get("owner_identity_id", "") if certified else "",
        "supplier_id": certified.get("supplier_id", "") if certified else "",
        "supplier_name": certified.get("display_name", "") if certified else "",
        "listing_id": active_listing.get("listing_id", "") if active_listing else "",
        "listing_title": active_listing.get("title", "") if active_listing else "",
    }
    snapshot["partner_supply"] = partner_supply.status()
    snapshot["travel_policy"] = travel_supply_policy.public_policy()
    return snapshot


@bp.get("/travel")
def public_travel():
    """Render the sovereign hybrid OAP Travel catalogue."""

    try:
        catalogue = _hybrid_catalogue(
            category=request.args.get("category"),
            limit=request.args.get("limit", "24"),
        )
    except ValueError as exc:
        catalogue = {
            "component": "OAP Travel Catalogue",
            "direct": {"offers": [], "count": 0},
            "partner": {"offers": [], "count": 0},
            "direct_count": 0,
            "partner_count": 0,
            "policy": travel_supply_policy.public_policy(),
            "error": str(exc),
        }
    return _no_store(make_response(render_template("travel.html", catalogue=catalogue)))


@bp.get("/travel/direct")
def public_marketplace():
    try:
        offers = travel_marketplace.public_offers(
            category=request.args.get("category"),
            country=request.args.get("country"),
            limit=request.args.get("limit", "24"),
        )
    except ValueError as exc:
        offers = {
            "component": "OAP Direct",
            "ready": True,
            "offers": [],
            "count": 0,
            "error": str(exc),
        }
    return _no_store(
        make_response(render_template("travel_direct.html", marketplace=offers))
    )


@bp.get("/travel/direct/api/offers")
def public_offers():
    try:
        result = travel_marketplace.public_offers(
            category=request.args.get("category"),
            country=request.args.get("country"),
            limit=request.args.get("limit", "24"),
        )
    except ValueError as exc:
        return _error("invalid_discovery_filter", str(exc)[:120], 400)
    return _no_store(make_response(jsonify(result)))


@bp.post("/travel/direct/api/quote")
def direct_quote():
    """Re-check price and capacity without creating a reservation or hold."""

    try:
        result = travel_marketplace.quote_direct(_json_payload())
    except (TypeError, ValueError) as exc:
        return _error("invalid_booking_quote", str(exc)[:140], 400)
    except RuntimeError as exc:
        return _error("booking_runtime_unavailable", str(exc)[:140], 503)
    return _no_store(make_response(jsonify(result)))


@bp.post("/travel/direct/api/hold")
@web_security.login_required(api=True)
def direct_hold():
    """Place a 15-minute capacity hold for the authenticated buyer."""

    return _buyer_write(travel_marketplace.create_buyer_hold)


@bp.post("/travel/direct/api/reservations")
@web_security.login_required(api=True)
def direct_reservation():
    """Convert the buyer's hold after an explicit Human confirmation click."""

    return _buyer_write(travel_marketplace.create_buyer_reservation)


@bp.get("/travel/partner/api/offers")
def public_partner_offers():
    try:
        result = partner_supply.public_offers(
            category=request.args.get("category"),
            limit=request.args.get("limit", "24"),
        )
    except ValueError as exc:
        return _error("invalid_partner_filter", str(exc)[:120], 400)
    return _no_store(make_response(jsonify(result)))


@bp.get("/travel/api/catalogue")
def public_catalogue():
    """Return Direct and Partner Supply as explicit, ordered source groups."""

    try:
        result = _hybrid_catalogue(
            category=request.args.get("category"),
            country=request.args.get("country"),
            limit=request.args.get("limit", "24"),
        )
    except ValueError as exc:
        return _error("invalid_catalogue_filter", str(exc)[:120], 400)
    return _no_store(make_response(jsonify(result)))


@bp.get("/mission/supply")
@web_security.login_required(founder_only=True)
def founder_dashboard():
    snapshot = _operator_snapshot()
    return _no_store(
        make_response(
            render_template(
                "travel_supply_control.html",
                supply=snapshot,
                csrf_token=web_security.csrf_token(),
            )
        )
    )


@bp.get("/mission/supply/status")
@web_security.login_required(api=True, founder_only=True)
def founder_status():
    return _no_store(make_response(jsonify(_operator_snapshot())))


@bp.get("/mission/supply/partner/status")
@web_security.login_required(api=True, founder_only=True)
def founder_partner_status():
    return _no_store(make_response(jsonify(partner_supply.status())))


@bp.post("/mission/supply/partner/import")
@web_security.login_required(api=True, founder_only=True)
def founder_partner_import():
    return _founder_write(partner_supply.import_snapshot)


@bp.post("/mission/supply/suppliers")
@web_security.login_required(api=True, founder_only=True)
def create_supplier():
    return _founder_write(travel_marketplace.create_supplier)


@bp.post("/mission/supply/suppliers/review")
@web_security.login_required(api=True, founder_only=True)
def submit_supplier():
    return _founder_write(travel_marketplace.submit_supplier)


@bp.post("/mission/supply/suppliers/certify")
@web_security.login_required(api=True, founder_only=True)
def certify_supplier():
    return _founder_write(travel_marketplace.certify_supplier)


@bp.post("/mission/supply/listings")
@web_security.login_required(api=True, founder_only=True)
def create_listing():
    return _founder_write(travel_marketplace.create_listing)


@bp.post("/mission/supply/listings/activate")
@web_security.login_required(api=True, founder_only=True)
def activate_listing():
    return _founder_write(travel_marketplace.activate_listing)


@bp.post("/mission/supply/inventory")
@web_security.login_required(api=True, founder_only=True)
def set_inventory():
    return _founder_write(travel_marketplace.set_inventory)


@bp.post("/mission/supply/reservations/confirm")
@web_security.login_required(api=True, founder_only=True)
def confirm_reservation():
    if not web_security.csrf_valid(request):
        return _error("csrf_failed", "The secure session expired.", 403)
    try:
        payload = _json_payload()
        result = travel_marketplace.confirm_supplier_reservation(
            payload,
            owner_identity_id=web_security.authenticated_identity(),
        )
    except PermissionError as exc:
        return _error("supplier_confirmation_not_authorized", str(exc)[:140], 403)
    except (TypeError, ValueError) as exc:
        return _error("invalid_supplier_confirmation", str(exc)[:140], 400)
    except RuntimeError as exc:
        return _error("booking_runtime_unavailable", str(exc)[:140], 503)
    return _no_store(make_response(jsonify(result)))
