"""Public partner-supply discovery and Founder-only audited snapshot import."""
from __future__ import annotations

from flask import Blueprint, jsonify, make_response, request

from . import partner_supply, web_security

bp = Blueprint("partner_supply", __name__)


def _no_store(response):
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


def _error(code: str, message: str, status_code: int):
    return _no_store(
        make_response(jsonify(error={"code": code, "message": message}), status_code)
    )


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


@bp.get("/mission/supply/partner/status")
@web_security.login_required(api=True, founder_only=True)
def founder_partner_status():
    return _no_store(make_response(jsonify(partner_supply.status())))


@bp.post("/mission/supply/partner/import")
@web_security.login_required(api=True, founder_only=True)
def founder_partner_import():
    if not web_security.csrf_valid(request):
        return _error("csrf_failed", "The secure session expired.", 403)
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return _error("invalid_partner_snapshot", "json_object_required", 400)
    try:
        result = partner_supply.import_snapshot(payload)
    except PermissionError as exc:
        return _error("human_authority_required", str(exc)[:140], 403)
    except (TypeError, ValueError) as exc:
        return _error("invalid_partner_snapshot", str(exc)[:140], 400)
    except RuntimeError as exc:
        return _error("partner_supply_unavailable", str(exc)[:140], 503)
    return _no_store(make_response(jsonify(result)))
