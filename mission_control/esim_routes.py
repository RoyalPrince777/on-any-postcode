"""Protected eSIM provisioning API.

User requests are authenticated. Consequential lifecycle actions are Founder-only and
remain fail-closed until a real provider adapter is attached to the provisioning core.
"""
from __future__ import annotations

from flask import Blueprint, jsonify, make_response, request

from . import esim_provisioning, web_security

bp = Blueprint("esim_provisioning", __name__)


def _response(payload: dict, status: int = 200):
    response = make_response(jsonify(payload), status)
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


def _csrf_guard():
    if not web_security.csrf_valid(request):
        return _response({"error": {"code": "csrf_failed"}}, 403)
    return None


def _error(exc: Exception):
    code = str(exc) or type(exc).__name__
    if isinstance(exc, KeyError):
        return _response({"error": {"code": "esim_request_not_found"}}, 404)
    if isinstance(exc, PermissionError):
        return _response({"error": {"code": code}}, 403)
    if isinstance(exc, ValueError):
        return _response({"error": {"code": code}}, 400)
    if isinstance(exc, RuntimeError):
        return _response({"error": {"code": code}}, 503)
    return _response({"error": {"code": "esim_unavailable"}}, 503)


@bp.post("/esim/requests")
@web_security.login_required(api=True)
def create_request():
    """Create an authenticated eSIM connectivity request; never auto-activate."""

    if guard := _csrf_guard():
        return guard
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return _response({"error": {"code": "json_object_required"}}, 400)
    try:
        item = esim_provisioning.CORE.request(
            subject_id=web_security.authenticated_identity(),
            purpose=body.get("purpose"),
        )
        return _response({"esim_request": item}, 201)
    except Exception as exc:  # noqa: BLE001 - redact implementation details.
        return _error(exc)


@bp.get("/mission/esim/requests/<request_id>")
@web_security.login_required(api=True, founder_only=True)
def get_request(request_id: str):
    try:
        return _response({"esim_request": esim_provisioning.CORE.get(request_id)})
    except Exception as exc:  # noqa: BLE001
        return _error(exc)


@bp.get("/mission/esim/requests/<request_id>/events")
@web_security.login_required(api=True, founder_only=True)
def get_events(request_id: str):
    try:
        return _response({"events": esim_provisioning.CORE.events(request_id)})
    except Exception as exc:  # noqa: BLE001
        return _error(exc)


def _founder_action(request_id: str, action: str):
    if guard := _csrf_guard():
        return guard
    try:
        core = esim_provisioning.CORE
        if action == "approve":
            result = core.approve(
                request_id,
                founder_identity=web_security.authenticated_identity(),
            )
        else:
            result = getattr(core, action)(request_id)
        return _response({"esim_request": result})
    except Exception as exc:  # noqa: BLE001
        return _error(exc)


@bp.post("/mission/esim/requests/<request_id>/approve")
@web_security.login_required(api=True, founder_only=True)
def approve(request_id: str):
    return _founder_action(request_id, "approve")


@bp.post("/mission/esim/requests/<request_id>/provision")
@web_security.login_required(api=True, founder_only=True)
def provision(request_id: str):
    return _founder_action(request_id, "provision")


@bp.post("/mission/esim/requests/<request_id>/suspend")
@web_security.login_required(api=True, founder_only=True)
def suspend(request_id: str):
    return _founder_action(request_id, "suspend")


@bp.post("/mission/esim/requests/<request_id>/resume")
@web_security.login_required(api=True, founder_only=True)
def resume(request_id: str):
    return _founder_action(request_id, "resume")


@bp.post("/mission/esim/requests/<request_id>/revoke")
@web_security.login_required(api=True, founder_only=True)
def revoke(request_id: str):
    return _founder_action(request_id, "revoke")
