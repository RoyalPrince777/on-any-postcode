"""Founder-only Company Intelligence dashboard."""
from __future__ import annotations

from flask import Blueprint, jsonify, make_response, render_template

from . import company_intelligence, company_intelligence_runtime, web_security

bp = Blueprint("company_intelligence", __name__)


def _no_store(response):
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


@bp.get("/company-intelligence")
@web_security.login_required(api=False, founder_only=True)
def dashboard():
    identity_id = web_security.authenticated_identity()
    runtime = company_intelligence_runtime.projection(identity_id)
    return _no_store(
        make_response(
            render_template(
                "company_intelligence.html",
                core=company_intelligence.status(),
                runtime=runtime,
            )
        )
    )


@bp.get("/company-intelligence/status")
@web_security.login_required(api=True, founder_only=True)
def status():
    identity_id = web_security.authenticated_identity()
    return _no_store(
        make_response(
            jsonify(
                {
                    "core": company_intelligence.status(),
                    "runtime": company_intelligence_runtime.projection(identity_id),
                }
            )
        )
    )
