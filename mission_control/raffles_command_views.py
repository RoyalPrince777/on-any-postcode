"""Founder-only Raffles review interface. No live prize or financial actions."""
from __future__ import annotations

import sqlite3
from pathlib import Path

from flask import Blueprint, jsonify, make_response, render_template, request

from oap.everyday import catalogue
from oap.raffles_durable import set_stop
from oap.raffles_mind import assess
from oap.raffles_soul import review

from . import authority, config, postgres_db, web_security

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


@bp.get("/everyday")
@web_security.login_required(founder_only=True)
def everyday_dashboard():
    response = make_response(render_template(
        "everyday_command.html", programme=catalogue()
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


@bp.post("/stop-control")
@web_security.login_required(api=True, founder_only=True)
def stop_control():
    """Only actual canonical read-back earns a STOP/recovery acknowledgement."""
    if not web_security.csrf_valid(request):
        return _reply({"ok": False, "outcome": "BLOCKED_CSRF"}, 403)
    body = request.get_json(silent=True)
    if not isinstance(body, dict) or body.get("action") not in ("STOP", "RECOVER"):
        return _reply({"ok": False, "outcome": "BLOCKED_UNKNOWN_ACTION"}, 400)
    user = web_security.current_authenticated_user()
    if not user:
        return _reply({"ok": False, "outcome": "BLOCKED_AUTHENTICATION"}, 401)
    campaign_id = body.get("campaign_id")
    if not isinstance(campaign_id, str) or campaign_id != "everyday-rewards":
        return _reply({"ok": False, "outcome": "BLOCKED_CAMPAIGN_ID"}, 400)
    database = Path(config.OAP_DATABASE_PATH)
    if not database.is_file():
        return _reply({"ok": False, "outcome": "BLOCKED_CANONICAL_DB_UNAVAILABLE"}, 503)
    try:
        actor = str(user["id"])
        if body["action"] == "RECOVER":
            with postgres_db.connect(readonly=True) as canonical:
                authority.require_human_authority(canonical, actor)
        with sqlite3.connect(database, timeout=3) as connection:
            result = set_stop(
                connection, campaign_id=campaign_id, actor=actor,
                action=body["action"],
                authority_checker=(lambda candidate: candidate == actor)
                if body["action"] == "RECOVER" else None,
            )
            # Read back the persisted state from the same canonical database.
            from oap.raffles_durable import status

            persisted = status(connection, campaign_id)
            if persisted["stopped"] is not result["stopped"] or (
                persisted["revision"] != result["revision"]
            ):
                raise RuntimeError("canonical_readback_mismatch")
        return _reply({"ok": True, **result})
    except PermissionError:
        return _reply({"ok": False, "outcome": "BLOCKED_FOUNDER_AUTHORITY"}, 403)
    except (RuntimeError, sqlite3.Error, OSError, ValueError):
        return _reply({"ok": False, "outcome": "BLOCKED_DURABLE_RUNTIME_UNAVAILABLE"}, 503)
