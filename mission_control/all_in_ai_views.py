"""Founder-only ALL IN A.I. Command Center surface."""

from flask import Blueprint, jsonify, make_response

from . import all_in_ai, web_security

bp = Blueprint("all_in_ai", __name__)


def _no_store(response):
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


@bp.get("/all-in-ai")
@web_security.login_required(api=True, founder_only=True)
def all_in_ai_status():
    return _no_store(make_response(jsonify(all_in_ai.status())))
