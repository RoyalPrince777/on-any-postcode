"""Founder-only Raffles review interface. No live prize or financial actions."""
from __future__ import annotations

from flask import Blueprint, jsonify, make_response, render_template, request

from oap.raffles_mind import assess
from oap.raffles_soul import review

from . import web_security

bp = Blueprint("raffles_command", __name__, url_prefix="/mission/raffles")


def _reply(body: dict[str, object], status: int = 200):
    response = make_response(jsonify(body), status)
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


@bp.get("")
@web_security.login_required(founder_only=True)
def dashboard():
    response = make_response(render_template(
        "raffles_command.html", csrf_token=web_security.csrf_token()
    ))
    response.headers["Cache-Control"] = "no-store"
    return response


@bp.post("/command")
@web_security.login_required(api=True, founder_only=True)
def command():
    if not web_security.csrf_valid(request):
        return _reply({"ok": False, "outcome": "BLOCKED_CSRF"}, 403)
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return _reply({"ok": False, "outcome": "BLOCKED_INVALID_JSON"}, 400)
    action = body.get("action")
    if action == "REVIEW":
        if not isinstance(body.get("evidence", {}), dict):
            return _reply({"ok": False, "outcome": "BLOCKED_INVALID_EVIDENCE"}, 400)
        result = assess(territory=body.get("territory", ""),
                        kind=body.get("kind", ""),
                        evidence=body.get("evidence", {}),
                        sponsor_funded=body.get("sponsor_funded") is True,
                        cash_required=body.get("cash_required") is True)
        soul = review(evidence=body.get("evidence", {}),
                      territory=str(body.get("territory", "")))
        return _reply({"ok": True, "outcome": str(result.decision.value),
                       "reasons": result.reasons, "missing": result.missing,
                       "soul_missing": soul.missing,
                       "release_allowed": False, "execution_granted": False,
                       "evidence_verified": False, "actual_matrix_votes": []})
    # STOP/RECOVER are NOT wired to durable canonical audit yet. Do not pretend
    # that an HTTP acknowledgement is durable STOP or Founder approval.
    if action in ("STOP", "RECOVER", "APPROVE_FOR_REVIEW", "CONTINUE",
                  "OPEN_ENTRIES", "TAKE_PAYMENT", "PUBLISH", "SELECT_WINNER"):
        return _reply({"ok": False, "outcome": "BLOCKED_CANONICAL_RUNTIME_NOT_WIRED",
                       "execution_granted": False}, 423)
    return _reply({"ok": False, "outcome": "BLOCKED_UNKNOWN_ACTION"}, 400)
