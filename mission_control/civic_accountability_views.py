"""Founder-private read-only civic accountability endpoint."""
from __future__ import annotations

from flask import Blueprint, jsonify, make_response

from . import civic_accountability_review, web_security

bp = Blueprint("civic_accountability", __name__)


@bp.get("/status")
@web_security.login_required(api=True, founder_only=True)
def civic_status():
    """No writes, no new agent identity or activation authority."""
    response = make_response(jsonify(civic_accountability_review.civic_accountability_snapshot()))
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response
