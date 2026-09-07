"""Founder-only read-only All Intelligence dashboard."""

from __future__ import annotations

from flask import Blueprint, jsonify, make_response, render_template

from . import all_intelligence, intelligence_runtime_proof, web_security

bp = Blueprint(
    "all_intelligence",
    __name__,
    url_prefix="/mission/intelligence",
    template_folder="templates",
)


def _no_store(response):
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


@bp.get("")
@bp.get("/")
@web_security.login_required(founder_only=True)
def dashboard():
    """Render the complete governed Intelligence hierarchy without actions."""

    return _no_store(
        make_response(
            render_template(
                "all_intelligence.html",
                intelligence=all_intelligence.public_safe_status(),
                runtime=intelligence_runtime_proof.status(),
            )
        )
    )


@bp.get("/status")
@web_security.login_required(api=True, founder_only=True)
def status():
    """Return the Founder-safe All Intelligence status projection."""

    return _no_store(make_response(jsonify(all_intelligence.public_safe_status())))


@bp.get("/runtime")
@web_security.login_required(api=True, founder_only=True)
def runtime():
    """Return bounded/live/full runtime proof without performing network calls."""

    return _no_store(make_response(jsonify(intelligence_runtime_proof.status())))
