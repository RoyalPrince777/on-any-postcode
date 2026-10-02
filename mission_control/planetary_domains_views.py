"""Founder-only OAP Planetary Intelligence dashboards."""
from __future__ import annotations

from flask import Blueprint, abort, jsonify, make_response, render_template

from . import planetary_domains, web_security

bp = Blueprint(
    "planetary_domains",
    __name__,
    url_prefix="/mission/planetary",
    template_folder="templates",
)


def _no_store(response):
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


def _page(*, selected=None, focus: str = "overview"):
    return _no_store(
        make_response(
            render_template(
                "planetary_domains.html",
                planetary=planetary_domains.public_safe_status(),
                selected=selected,
                focus=focus,
            )
        )
    )


@bp.get("")
@bp.get("/")
@web_security.login_required(founder_only=True)
def dashboard():
    return _page()


@bp.get("/domain/<domain_id>")
@web_security.login_required(founder_only=True)
def domain_dashboard(domain_id: str):
    try:
        selected = planetary_domains.domain_status(domain_id)
    except KeyError:
        abort(404)
    return _page(selected=selected, focus="domain")


@bp.get("/cyber")
@web_security.login_required(founder_only=True)
def cyber_dashboard():
    return _page(focus="cyber")


@bp.get("/smi-fusion")
@web_security.login_required(founder_only=True)
def smi_fusion_dashboard():
    return _page(focus="fusion")


@bp.get("/status")
@web_security.login_required(api=True, founder_only=True)
def status():
    return _no_store(make_response(jsonify(planetary_domains.public_safe_status())))


@bp.get("/domain/<domain_id>/status")
@web_security.login_required(api=True, founder_only=True)
def domain_status(domain_id: str):
    try:
        payload = planetary_domains.domain_status(domain_id)
    except KeyError:
        abort(404)
    return _no_store(make_response(jsonify(payload)))
