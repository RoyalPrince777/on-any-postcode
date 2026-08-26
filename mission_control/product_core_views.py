"""Authenticated first-party APIs for OAP Tune, Commerce and Post organs."""
from __future__ import annotations

from flask import Blueprint, jsonify, make_response, request

from . import product_core_services, product_cores, product_store, public_store, web_security

bp = Blueprint("product_core_organs", __name__)
_store = product_cores.PostgresProductCoreStore()


def _no_store(response):
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


def _error(code: str, message: str, status_code: int):
    return _no_store(
        make_response(jsonify(error={"code": code, "message": message}), status_code)
    )


def _identity(*, sync: bool = False) -> str:
    identity_id = web_security.authenticated_identity()
    if sync:
        user = web_security.current_authenticated_user()
        if user is None:
            raise PermissionError("authentication_required")
        public_store.ensure_authenticated_user(
            str(user["id"]),
            email=str(user["email"]),
            display_name=str(user["name"]),
            email_verified=bool(user.get("email_verified")),
        )
    return identity_id


def _payload() -> dict[str, object]:
    value = request.get_json(silent=True)
    if not isinstance(value, dict):
        raise ValueError("json_object_required")
    return value


def _write_allowed() -> bool:
    return web_security.csrf_valid(request)


def _handle_write(action):
    if not _write_allowed():
        return _error("csrf_failed", "The secure session expired. Refresh and try again.", 403)
    try:
        return _no_store(make_response(jsonify(action()), 201))
    except PermissionError as exc:
        return _error("permission_denied", str(exc), 403)
    except ValueError as exc:
        return _error("invalid_request", str(exc), 400)
    except (public_store.PublicStoreUnavailable, product_store.ProductStoreUnavailable, RuntimeError):
        return _error("organ_unavailable", "The OAP organ store is temporarily unavailable.", 503)


@bp.get("/status")
@web_security.login_required(api=True)
def all_organs_status():
    try:
        return _no_store(
            make_response(jsonify(product_core_services.organ_status(_identity())))
        )
    except (ValueError, RuntimeError):
        return _error("organ_unavailable", "Product organ status is temporarily unavailable.", 503)


@bp.get("/tune")
@web_security.login_required(api=True)
def tune_status():
    try:
        return _no_store(make_response(jsonify(product_core_services.tune_dashboard(_identity()))))
    except (ValueError, RuntimeError):
        return _error("tune_unavailable", "OAP Tune Core is temporarily unavailable.", 503)


@bp.post("/tune/releases")
@web_security.login_required(api=True)
def create_release():
    def action():
        payload = _payload()
        return _store.create_release(
            owner_identity_id=_identity(sync=True),
            title=payload.get("title"),
            release_type=payload.get("release_type"),
            idempotency_key=payload.get("idempotency_key"),
        )

    return _handle_write(action)


@bp.post("/tune/releases/<release_id>/tracks")
@web_security.login_required(api=True)
def add_track(release_id: str):
    def action():
        payload = _payload()
        return _store.add_track(
            owner_identity_id=_identity(sync=True),
            release_id=release_id,
            title=payload.get("title"),
            position=payload.get("position"),
            media_ref=payload.get("media_ref"),
            duration_ms=payload.get("duration_ms"),
            explicit=bool(payload.get("explicit", False)),
        )

    return _handle_write(action)


@bp.post("/tune/releases/<release_id>/review")
@web_security.login_required(api=True)
def review_release(release_id: str):
    return _handle_write(
        lambda: _store.submit_release_for_review(
            owner_identity_id=_identity(sync=True), release_id=release_id
        )
    )


@bp.post("/tune/playlists")
@web_security.login_required(api=True)
def create_playlist():
    def action():
        payload = _payload()
        return _store.create_playlist(
            owner_identity_id=_identity(sync=True),
            title=payload.get("title"),
            visibility=payload.get("visibility", "PRIVATE"),
        )

    return _handle_write(action)


@bp.post("/tune/playlists/<playlist_id>/tracks")
@web_security.login_required(api=True)
def add_playlist_track(playlist_id: str):
    def action():
        payload = _payload()
        return product_core_services.add_playlist_track(
            owner_identity_id=_identity(sync=True),
            playlist_id=playlist_id,
            track_id=payload.get("track_id"),
            position=payload.get("position"),
        )

    return _handle_write(action)


@bp.get("/commerce")
@web_security.login_required(api=True)
def commerce_status():
    try:
        return _no_store(
            make_response(jsonify(product_core_services.commerce_dashboard(_identity())))
        )
    except (ValueError, RuntimeError):
        return _error("commerce_unavailable", "OAP Commerce Core is temporarily unavailable.", 503)


@bp.post("/commerce/storefront")
@web_security.login_required(api=True)
def create_storefront():
    def action():
        payload = _payload()
        return _store.create_storefront(
            seller_identity_id=_identity(sync=True),
            store_name=payload.get("store_name"),
            slug=payload.get("slug"),
        )

    return _handle_write(action)


@bp.post("/commerce/products")
@web_security.login_required(api=True)
def create_product():
    def action():
        payload = _payload()
        product_id = product_store.create_product(
            _identity(sync=True),
            name=payload.get("name"),
            description=payload.get("description"),
            price=payload.get("price"),
        )
        return {
            "product_id": product_id,
            "payment_capture_performed": False,
            "external_fulfilment_performed": False,
        }

    return _handle_write(action)


@bp.post("/commerce/orders")
@web_security.login_required(api=True)
def create_order():
    def action():
        payload = _payload()
        return _store.create_order_intent(
            buyer_identity_id=_identity(sync=True),
            product_id=payload.get("product_id"),
            quantity=payload.get("quantity", 1),
            idempotency_key=payload.get("idempotency_key"),
        )

    return _handle_write(action)


@bp.get("/post")
@web_security.login_required(api=True)
def post_status():
    try:
        return _no_store(make_response(jsonify(product_core_services.post_dashboard(_identity()))))
    except (ValueError, RuntimeError):
        return _error("post_unavailable", "OAP Post Core is temporarily unavailable.", 503)


@bp.post("/post/requests")
@web_security.login_required(api=True)
def create_post_request():
    def action():
        payload = _payload()
        details = payload.get("details")
        if details is not None and not isinstance(details, dict):
            raise ValueError("post_office_details_must_be_object")
        return _store.create_post_office_request(
            identity_id=_identity(sync=True),
            service_type=payload.get("service_type"),
            details=details,
            idempotency_key=payload.get("idempotency_key"),
            post_office_id=payload.get("post_office_id"),
        )

    return _handle_write(action)


@bp.post("/post/parcels")
@web_security.login_required(api=True)
def create_parcel():
    def action():
        payload = _payload()
        return _store.create_parcel_intent(
            owner_identity_id=_identity(sync=True),
            direction=payload.get("direction"),
            idempotency_key=payload.get("idempotency_key"),
            post_office_id=payload.get("post_office_id"),
        )

    return _handle_write(action)
