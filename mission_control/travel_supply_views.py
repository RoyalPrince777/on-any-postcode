"""OAP Direct, Partner Supply and registered public ecosystem surfaces."""
from __future__ import annotations

from flask import Blueprint, jsonify, make_response, render_template, request

from . import partner_supply, travel_marketplace, web_security
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
    """Return direct and partner supply as explicit groups, never fake one source."""

    category = request.args.get("category")
    limit = request.args.get("limit", "24")
    country = request.args.get("country")
    try:
        direct = travel_marketplace.public_offers(
            category=category,
            country=country,
            limit=limit,
        )
        partner = partner_supply.public_offers(category=category, limit=limit)
    except ValueError as exc:
        return _error("invalid_catalogue_filter", str(exc)[:120], 400)
    result = {
        "component": "OAP Travel Catalogue",
        "direct": direct,
        "partner": partner,
        "direct_count": int(direct.get("count", 0)),
        "partner_count": int(partner.get("count", 0)),
        "booking_com_required": False,
        "partner_supply_is_replaceable": True,
        "automatic_quality_ranking_across_unmatched_offers": False,
        "external_provider_authority": False,
        "human_authority_final": True,
    }
    return _no_store(make_response(jsonify(result)))


@bp.get("/mission/supply")
@web_security.login_required(founder_only=True)
def founder_dashboard():
    snapshot = travel_marketplace.founder_snapshot()
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
    result = travel_marketplace.founder_snapshot()
    result["partner_supply"] = partner_supply.status()
    return _no_store(make_response(jsonify(result)))


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
