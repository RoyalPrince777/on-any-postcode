"""Private Founder HOLD/BLOCK endpoint; never an approval or vote producer."""
from __future__ import annotations

from flask import Blueprint, jsonify, make_response, request

from . import matrix_founder_decisions, web_security

bp = Blueprint("matrix_founder_decisions", __name__, url_prefix="/mission/matrix-decisions")


def _response(payload, status=200):
    response = make_response(jsonify(payload), status)
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


@bp.post("/hold")
@web_security.login_required(api=True, founder_only=True)
def record_hold():
    if not web_security.csrf_valid(request):
        return _response({"error": {"code": "csrf_failed"}}, 403)
    user = web_security.current_authenticated_user()
    if not user:
        return _response({"error": {"code": "authentication_required"}}, 401)
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return _response({"error": {"code": "invalid_json"}}, 400)
    try:
        result = matrix_founder_decisions.record_hold(
            identity_id=str(user["id"]),
            signal=body.get("signal"),
            decision=body.get("decision"),
            reason=body.get("reason"),
        )
    except PermissionError:
        return _response({"error": {"code": "human_authority_required"}}, 403)
    except (ValueError, TypeError):
        return _response({"error": {"code": "invalid_review"}}, 400)
    if result["state"] != "founder_hold_recorded":
        return _response(result, 503)
    return _response(result, 201)
