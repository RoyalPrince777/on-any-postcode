"""Private Mission Control views for the redacted OAP Provider Fabric."""

from __future__ import annotations

from flask import Blueprint, jsonify, make_response, render_template

from . import provider_fabric, web_security

bp = Blueprint("provider_fabric", __name__, template_folder="templates")


def _no_store(response):
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


@bp.get("/providers")
@web_security.login_required()
def provider_dashboard():
    """Render provider readiness without exposing credentials or controls."""

    response = make_response(
        render_template(
            "provider_fabric.html",
            fabric=provider_fabric.get_private_provider_fabric(),
        )
    )
    return _no_store(response)


@bp.get("/providers/status")
@web_security.login_required(api=True)
def provider_status():
    """Return coarse provider readiness only to a signed-in identity."""

    return _no_store(make_response(jsonify(provider_fabric.get_coarse_provider_status())))
