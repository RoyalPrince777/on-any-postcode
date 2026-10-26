"""OAP Commons: authenticated voluntary member intake, not public elections."""
from __future__ import annotations

from flask import Blueprint, jsonify, make_response, redirect, render_template, request, url_for

from . import oap_commons, public_store, web_security

bp = Blueprint("oap_commons", __name__, template_folder="templates")


def _safe(response):
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


def _error(code: str, code_status: int):
    return _safe(make_response(jsonify(error={"code": code}), code_status))


@bp.get("/commons")
@web_security.login_required()
def commons_home():
    user = web_security.current_authenticated_user()
    try:
        proposals = oap_commons.mine(user["id"])
    except oap_commons.CommonsUnavailable:
        return _safe(make_response(render_template(
            "oap_commons.html", proposals=(), csrf=web_security.csrf_token(),
            store_available=False, submitted=False,
        ), 503))
    return _safe(make_response(render_template(
        "oap_commons.html", proposals=proposals,
        csrf=web_security.csrf_token(), store_available=True,
        submitted=request.args.get("submitted") == "1",
    )))


@bp.post("/commons/proposals")
@web_security.login_required(api=True)
def commons_submit():
    if not web_security.csrf_valid(request):
        return _error("csrf_failed", 403)
    data = request.get_json(silent=True) if request.is_json else request.form
    if data is None or not hasattr(data, "get"):
        return _error("invalid_commons_request", 400)
    consent = (
        data.get("consent") is True if request.is_json
        else data.get("consent") == "yes"
    )
    try:
        validated = oap_commons.validate_proposal(
            data.get("title"), data.get("body"), consent,
        )
    except ValueError as exc:
        return _error(str(exc), 400)
    user = web_security.current_authenticated_user()
    try:
        public_store.ensure_authenticated_user(
            str(user["id"]),
            email=str(user["email"]),
            display_name=str(user["name"]),
            email_verified=bool(user["email_verified"]),
            store_email=False,
        )
        result = oap_commons.submit(str(user["id"]), **validated, consent=True)
    except ValueError as exc:
        if str(exc) == "commons_submission_rate_limited":
            return _error("commons_submission_rate_limited", 429)
        return _error("invalid_commons_submission", 400)
    except (public_store.PublicStoreUnavailable, oap_commons.CommonsUnavailable):
        return _error("commons_submission_unavailable", 503)
    if request.is_json:
        return _safe(make_response(jsonify(result), 201))
    return _safe(make_response(redirect(url_for("oap_commons.commons_home", submitted=1), 303)))


@bp.get("/commons/status")
@web_security.login_required(api=True)
def commons_status():
    return _safe(make_response(jsonify(oap_commons.status())))
