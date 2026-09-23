"""Read-only OAP Store catalogue entry for Mail; never an installer."""
from __future__ import annotations

from flask import Blueprint, jsonify, make_response, render_template, url_for

from . import mail_store_listing

bp = Blueprint("oap_mail_store_catalog", __name__)


@bp.get("/oap-store/apps/oap.mail")
def mail_store_entry():
    """Show truthful release-pending Mail metadata without a package URL."""
    response = make_response(jsonify(mail_store_listing.listing()), 200)
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


@bp.get("/oap-store/apps/oap.mail/view")
def mail_store_detail():
    """Public first-party listing; private preview requires member login."""
    response = make_response(render_template(
        "oap_mail_store_detail.html",
        app=mail_store_listing.listing(),
        preview_path=url_for("oap_mail_private.mail_app"),
    ), 200)
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    return response
