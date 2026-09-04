"""OAP Direct travel marketplace and Founder-controlled supply surfaces."""
from __future__ import annotations

from flask import Blueprint, Response, jsonify, make_response, render_template, request

from . import listing_media, travel_marketplace, travel_supply_policy, web_security
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


def _enrich_photos(marketplace: dict) -> dict:
    offers = list(marketplace.get("offers") or [])
    photos = listing_media.photo_map(
        str(offer.get("listing_id") or "") for offer in offers
    )
    for offer in offers:
        listing_id = str(offer.get("listing_id") or "")
        gallery = photos.get(listing_id, [])
        offer["photos"] = gallery
        offer["photo_count"] = len(gallery)
        offer["cover_photo_url"] = gallery[0]["public_path"] if gallery else ""
    marketplace["offers"] = offers
    marketplace["listing_media"] = listing_media.status()
    return marketplace


def _catalogue(*, category: object = None, country: object = None, limit: object = 24) -> dict:
    direct = _enrich_photos(
        travel_marketplace.public_offers(
            category=category,
            country=country,
            limit=limit,
        )
    )
    policy = travel_supply_policy.public_policy()
    return {
        "component": "OAP Travel Catalogue",
        "direct": direct,
        "direct_count": int(direct.get("count", 0)),
        "source_order": list(travel_supply_policy.PREFERRED_SOURCE_ORDER),
        "policy": policy,
        "external_data_fetch_allowed": policy["external_data_fetch_allowed"],
        "external_catalogue_import_allowed": policy[
            "external_catalogue_import_allowed"
        ],
        "external_provider_authority": False,
        "human_authority_final": True,
    }


def _operator_snapshot() -> dict:
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
    photo_map = listing_media.photo_map(
        str(item.get("listing_id") or "") for item in listings
    )
    for item in listings:
        gallery = photo_map.get(str(item.get("listing_id") or ""), [])
        item["photos"] = gallery
        item["photo_count"] = len(gallery)
    active_listing = next(
        (item for item in listings if item.get("state") == "ACTIVE"),
        listings[0] if listings else None,
    )
    snapshot["listings"] = listings
    snapshot["operator"] = {
        "supplier_ready": certified is not None,
        "owner_identity_id": certified.get("owner_identity_id", "") if certified else "",
        "supplier_id": certified.get("supplier_id", "") if certified else "",
        "supplier_name": certified.get("display_name", "") if certified else "",
        "listing_id": active_listing.get("listing_id", "") if active_listing else "",
        "listing_title": active_listing.get("title", "") if active_listing else "",
    }
    snapshot["listing_media"] = listing_media.status()
    snapshot["travel_policy"] = travel_supply_policy.public_policy()
    return snapshot


@bp.get("/travel")
def public_travel():
    try:
        catalogue = _catalogue(
            category=request.args.get("category"),
            country=request.args.get("country"),
            limit=request.args.get("limit", "24"),
        )
    except ValueError as exc:
        catalogue = {
            "component": "OAP Travel Catalogue",
            "direct": {"offers": [], "count": 0},
            "direct_count": 0,
            "policy": travel_supply_policy.public_policy(),
            "error": str(exc),
        }
    return _no_store(make_response(render_template("travel.html", catalogue=catalogue)))


@bp.get("/travel/direct")
def public_marketplace():
    try:
        offers = _enrich_photos(
            travel_marketplace.public_offers(
                category=request.args.get("category"),
                country=request.args.get("country"),
                limit=request.args.get("limit", "24"),
            )
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
        result = _enrich_photos(
            travel_marketplace.public_offers(
                category=request.args.get("category"),
                country=request.args.get("country"),
                limit=request.args.get("limit", "24"),
            )
        )
    except ValueError as exc:
        return _error("invalid_discovery_filter", str(exc)[:120], 400)
    return _no_store(make_response(jsonify(result)))


@bp.get("/travel/direct/photos/<photo_id>")
def public_listing_photo(photo_id: str):
    try:
        item = listing_media.public_photo(photo_id)
    except ValueError:
        item = None
    if item is None:
        return _error("listing_photo_not_found", "Listing photo not found.", 404)
    data, content_type, digest = item
    response = Response(data, mimetype=content_type)
    response.headers["Cache-Control"] = "public, max-age=86400"
    response.headers["ETag"] = f'"{digest}"'
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


@bp.post("/travel/direct/api/quote")
def direct_quote():
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
    return _buyer_write(travel_marketplace.create_buyer_hold)


@bp.post("/travel/direct/api/reservations")
@web_security.login_required(api=True)
def direct_reservation():
    return _buyer_write(travel_marketplace.create_buyer_reservation)


@bp.get("/travel/partner/api/offers")
def retired_partner_offers():
    return _error(
        "partner_supply_removed",
        "Partner Supply is not part of OAP Travel. External data is fetched on demand only.",
        410,
    )


@bp.get("/travel/api/catalogue")
def public_catalogue():
    try:
        result = _catalogue(
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
    return _error(
        "partner_supply_removed",
        "External marketplace partnerships are disabled for OAP Travel.",
        410,
    )


@bp.post("/mission/supply/partner/import")
@web_security.login_required(api=True, founder_only=True)
def founder_partner_import():
    return _error(
        "partner_supply_removed",
        "External marketplace data cannot be imported as OAP Partner Supply.",
        410,
    )


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


@bp.post("/mission/supply/listings/photos")
@web_security.login_required(api=True, founder_only=True)
def add_listing_photo():
    return _founder_write(listing_media.add_photo)


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
