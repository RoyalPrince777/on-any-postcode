"""Founder-only SMI alignment and simple task debug routes."""
from __future__ import annotations

from flask import Blueprint, jsonify, make_response, request

from . import alignment_check, web_security

bp = Blueprint("alignment", __name__)


def _no_store(response):
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


@bp.get("/war-room/alignment")
@bp.get("/war-room/actions/alignment")
@bp.get("/alignment/status")
@web_security.login_required(api=True, founder_only=True)
def alignment_status():
    """Check public/menu alignment without exposing private state publicly."""

    return _no_store(make_response(jsonify(alignment_check.status())))


@bp.get("/war-room/thinking-signals")
@bp.get("/war-room/actions/thinking-signals")
@bp.get("/smi/thinking-signals")
@web_security.login_required(api=True, founder_only=True)
def thinking_signals():
    """Return private-safe visible SMI thinking/status signals."""

    return _no_store(make_response(jsonify(alignment_check.thinking_signals())))


@bp.get("/war-room/debug/simple-task")
@bp.get("/war-room/actions/simple-task-debug")
@web_security.login_required(api=True, founder_only=True)
def simple_task_debug():
    """Return the safe protocol for a simple task fix/debug loop."""

    return _no_store(
        make_response(
            jsonify(alignment_check.simple_task_debug(request.args.get("task")))
        )
    )


@bp.get("/war-room/debug/404")
@bp.get("/war-room/actions/404-check")
@web_security.login_required(api=True, founder_only=True)
def not_found_debug():
    """Return the private-safe 404 recovery check."""

    pack = alignment_check.simple_task_debug("404 public recovery check")
    pack["checks"] = {
        "public_404_simple": True,
        "public_404_has_private_debug": False,
        "public_404_routes": ("/", "/on-any-place", "/movement", "/travel/direct"),
        "war_room_owns_debug": True,
    }
    return _no_store(make_response(jsonify(pack)))
