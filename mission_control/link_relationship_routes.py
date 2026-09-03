"""Protected member routes for Link Request lifecycle."""
from __future__ import annotations

from flask import Blueprint, jsonify, redirect, request, url_for

from . import link_relationships, web_security

bp = Blueprint("link_relationships", __name__)


def _csrf_failure():
    return jsonify(error={"code": "csrf_failed"}), 403


@bp.post("/linkup/requests")
@web_security.login_required(api=True)
def create_request():
    if not web_security.csrf_valid(request):
        return _csrf_failure()
    user = web_security.current_authenticated_user()
    if not web_security.PUBLIC_WRITE_LIMITER.allow(str(user["id"])):
        return jsonify(error={"code": "rate_limited"}), 429
    try:
        link_relationships.request_link(str(user["id"]), request.form.get("recipient_id"))
    except ValueError as exc:
        return jsonify(error={"code": str(exc)}), 400
    except link_relationships.LinkRelationshipUnavailable:
        return jsonify(error={"code": "link_relationship_unavailable"}), 503
    return redirect(url_for("linkup_front_door"))


@bp.post("/linkup/requests/<request_id>/accept")
@web_security.login_required(api=True)
def accept_request(request_id: str):
    return _respond(request_id, "accepted")


@bp.post("/linkup/requests/<request_id>/decline")
@web_security.login_required(api=True)
def decline_request(request_id: str):
    return _respond(request_id, "declined")


def _respond(request_id: str, decision: str):
    if not web_security.csrf_valid(request):
        return _csrf_failure()
    user = web_security.current_authenticated_user()
    try:
        changed = link_relationships.respond(str(user["id"]), request_id, decision)
    except ValueError as exc:
        return jsonify(error={"code": str(exc)}), 400
    except link_relationships.LinkRelationshipUnavailable:
        return jsonify(error={"code": "link_relationship_unavailable"}), 503
    if not changed:
        return jsonify(error={"code": "link_request_not_found"}), 404
    return redirect(url_for("linkup_front_door"))


@bp.post("/linkup/requests/<request_id>/cancel")
@web_security.login_required(api=True)
def cancel_request(request_id: str):
    if not web_security.csrf_valid(request):
        return _csrf_failure()
    user = web_security.current_authenticated_user()
    try:
        changed = link_relationships.cancel(str(user["id"]), request_id)
    except ValueError as exc:
        return jsonify(error={"code": str(exc)}), 400
    except link_relationships.LinkRelationshipUnavailable:
        return jsonify(error={"code": "link_relationship_unavailable"}), 503
    if not changed:
        return jsonify(error={"code": "link_request_not_found"}), 404
    return redirect(url_for("linkup_front_door"))
