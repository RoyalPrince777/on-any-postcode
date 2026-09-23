"""Read-only OAP Store catalogue entry for Mail; never an installer."""
from __future__ import annotations

from flask import Blueprint, jsonify, make_response

from . import mail_store_listing

bp = Blueprint("oap_mail_store_catalog", __name__)


@bp.get("/oap-store/apps/oap.mail")
def mail_store_entry():
    """Show truthful release-pending Mail metadata without a package URL."""
    response = make_response(jsonify(mail_store_listing.listing()), 200)
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response
