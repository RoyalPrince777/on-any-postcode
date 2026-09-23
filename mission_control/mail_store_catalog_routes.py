"""Public Mail Store information only. No private Mail or install actions."""
from __future__ import annotations

from flask import Blueprint, jsonify, make_response, render_template

from . import mail_store_listing

bp = Blueprint("oap_mail_store_catalog", __name__)


@bp.after_request
def safe_catalogue_response(response):
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["X-Robots-Tag"] = "noindex, nofollow, noarchive"
    return response


@bp.get("/oap-store/apps/oap.mail")
def mail_store_entry():
    """Informational JSON; never an installer or delivery-status report."""
    return make_response(jsonify(mail_store_listing.listing()), 200)


@bp.get("/oap-store/apps/oap.mail/view")
def mail_store_detail():
    """Public first-party information; private Mail is not released here."""
    return make_response(render_template(
        "oap_mail_store_detail.html", app=mail_store_listing.listing()
    ), 200)
