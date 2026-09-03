"""Founder-only OAP Data product surface."""
from __future__ import annotations

from flask import Blueprint, jsonify, make_response, render_template

from . import authority, oap_data, postgres_db, web_security

bp = Blueprint("oap_data", __name__)


def _no_store(response):
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


def _require_human_authority() -> None:
    user = web_security.current_authenticated_user()
    if user is None:
        raise authority.HumanAuthorityRequired("authentication_required")
    try:
        with postgres_db.connect(readonly=True) as connection:
            authority.require_human_authority(connection, str(user["id"]))
    except authority.HumanAuthorityRequired:
        raise
    except Exception as exc:
        raise authority.AuthorityUnavailable("oap_data_authority_unavailable") from exc


@bp.get("/data")
@web_security.login_required()
def product_dashboard():
    """Render the private OAP Data product without exposing raw records."""

    try:
        _require_human_authority()
    except authority.HumanAuthorityRequired:
        return _no_store(make_response("Human Authority required.", 403))
    except authority.AuthorityUnavailable:
        return _no_store(make_response("OAP Data is temporarily unavailable.", 503))

    return _no_store(
        make_response(
            render_template("oap_data.html", oap_data=oap_data.get_product_status())
        )
    )


@bp.get("/data/status")
@web_security.login_required(api=True)
def product_status():
    """Return the same coarse Founder-only OAP Data product projection."""

    try:
        _require_human_authority()
    except authority.HumanAuthorityRequired:
        return _no_store(
            make_response(jsonify(error={"code": "human_authority_required"}), 403)
        )
    except authority.AuthorityUnavailable:
        return _no_store(
            make_response(jsonify(error={"code": "oap_data_unavailable"}), 503)
        )

    return _no_store(make_response(jsonify(oap_data.get_product_status())))
