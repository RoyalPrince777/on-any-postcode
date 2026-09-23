"""Founder-only Raffles review interface. No live prize or financial actions."""
from __future__ import annotations

import sqlite3
from pathlib import Path
from uuid import uuid4

from flask import Blueprint, jsonify, make_response, render_template, request

from oap.everyday import catalogue
from oap.everyday_records import propose_partner, propose_resource, records
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
        "everyday_command.html", programme=catalogue(),
        csrf_token=web_security.csrf_token()
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


@bp.get("/everyday/records")
@web_security.login_required(api=True, founder_only=True)
def everyday_records():
    """No schema creation or public claims; only private records already stored."""
    user = web_security.current_authenticated_user()
    if not user:
        return _reply({"ok": False, "outcome": "BLOCKED_AUTHENTICATION"}, 401)
    database = Path(config.OAP_DATABASE_PATH)
    if not database.is_file():
        return _reply({"ok": False, "outcome": "BLOCKED_CANONICAL_DB_UNAVAILABLE"}, 503)
    try:
        with sqlite3.connect(database.resolve().as_uri() + "?mode=ro",
                             uri=True, timeout=3) as connection:
            data = records(connection)
        return _reply({"ok": True, **data})
    except (sqlite3.Error, RuntimeError, OSError):
        return _reply({"ok": False, "outcome": "BLOCKED_EVERYDAY_SCHEMA_UNAVAILABLE"}, 503)


@bp.post("/everyday/propose")
@web_security.login_required(api=True, founder_only=True)
def everyday_propose():
    """Save only private unverified proposals, atomically with canonical audit."""
    if not web_security.csrf_valid(request):
        return _reply({"ok": False, "outcome": "BLOCKED_CSRF"}, 403)
    user = web_security.current_authenticated_user()
    if not user:
        return _reply({"ok": False, "outcome": "BLOCKED_AUTHENTICATION"}, 401)
    body = request.get_json(silent=True)
    if not isinstance(body, dict) or body.get("kind") not in ("partner", "resource"):
        return _reply({"ok": False, "outcome": "BLOCKED_INVALID_PROPOSAL"}, 400)
    database = Path(config.OAP_DATABASE_PATH)
    if not database.is_file():
        return _reply({"ok": False, "outcome": "BLOCKED_CANONICAL_DB_UNAVAILABLE"}, 503)
    try:
        with sqlite3.connect(database, timeout=3) as connection:
            record_id = str(uuid4())
            actor = str(user["id"])
            if body["kind"] == "partner":
                result = propose_partner(
                    connection, record_id=record_id,
                    organisation=body.get("organisation"),
                    prize=body.get("prize"), actor=actor,
                )
            else:
                result = propose_resource(
                    connection, record_id=record_id,
                    title=body.get("title"), url=body.get("url"),
                    source=body.get("source"),
                    checked_on=body.get("checked_on"), actor=actor,
                )
            # The receipt alone is insufficient: confirm the persisted row.
            observed = records(connection)
            chosen = observed["partners" if body["kind"] == "partner" else "resources"]
            if not any(row["id"] == record_id for row in chosen):
                raise RuntimeError("canonical_record_readback_missing")
        return _reply({"ok": True, **result, "public_listing_allowed": False,
                       "execution_granted": False}, 201)
    except (TypeError, ValueError):
        return _reply({"ok": False, "outcome": "BLOCKED_INVALID_PROPOSAL"}, 400)
    except (sqlite3.Error, RuntimeError, OSError):
        return _reply({"ok": False, "outcome": "BLOCKED_EVERYDAY_SCHEMA_OR_AUDIT"}, 503)
