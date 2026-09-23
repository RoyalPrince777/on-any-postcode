"""Public informational bank Store page; no installation or finance actions."""
from __future__ import annotations

from flask import Blueprint, jsonify, make_response, render_template

from . import bank_store_listing

bp = Blueprint("oap_bank_store_catalog", __name__)


@bp.after_request
def safe_catalogue_response(response):
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["X-Robots-Tag"] = "noindex, nofollow, noarchive"
    return response


@bp.get("/oap-store/apps/oap.usa_royalty_bank")
def bank_store_entry():
    return make_response(jsonify(bank_store_listing.listing()), 200)


@bp.get("/oap-store/apps/oap.usa_royalty_bank/view")
def bank_store_detail():
    return make_response(
        render_template("oap_bank_store_detail.html", app=bank_store_listing.listing()),
        200,
    )
