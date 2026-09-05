"""Private SIKA value and My Card dashboard routes."""
from __future__ import annotations

from flask import Blueprint, jsonify, make_response, render_template, request

from . import sika_value, web_security

bp = Blueprint("sika_value", __name__)


def _no_store(response):
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


def _founder_flag() -> bool:
    try:
        user = web_security.current_authenticated_user()
    except Exception:  # pragma: no cover - route decorator handles fail-closed auth.
        user = None
    if user is None:
        return False
    try:
        return bool(web_security.private_authority_allowed(user))
    except Exception:  # pragma: no cover
        return False


@bp.get("/sika")
@web_security.login_required(founder_only=True)
def dashboard():
    """Render the Founder SIKA value, badge and revenue command surface."""
    return _no_store(
        make_response(
            render_template(
                "sika_value.html",
                sika=sika_value.status(),
                my_card=sika_value.my_card(
                    display_name="Founder",
                    handle="@earthisourturf777",
                    founder=True,
                ),
            )
        )
    )


@bp.get("/sika/status")
@web_security.login_required(api=True, founder_only=True)
def dashboard_status():
    """Return safe SIKA readiness without money movement or bank authority."""
    return _no_store(make_response(jsonify(sika_value.status())))


@bp.get("/sika/my-card")
@web_security.login_required()
def my_card():
    """Render the OAP My Card identity layer for the current private session."""
    name = request.args.get("name") or "OAP Member"
    handle = request.args.get("handle") or "@oap"
    founder = _founder_flag()
    if founder:
        name = "Founder"
        handle = "@earthisourturf777"
    return _no_store(
        make_response(
            render_template(
                "sika_my_card.html",
                card=sika_value.my_card(name, handle, founder=founder),
            )
        )
    )


@bp.get("/sika/revenue")
@web_security.login_required(founder_only=True)
def revenue():
    """Render monetisation streams separately from bank/payment powers."""
    return _no_store(
        make_response(render_template("sika_revenue.html", sika=sika_value.status()))
    )


@bp.get("/sika/compliance")
@web_security.login_required(founder_only=True)
def compliance():
    """Render compliance locks that keep SIKA v1 out of regulated money movement."""
    return _no_store(
        make_response(render_template("sika_compliance.html", sika=sika_value.status()))
    )
