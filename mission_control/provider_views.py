"""Private Mission Control views for Provider Fabric and alignment truth."""

from __future__ import annotations

import json
import logging

from flask import Blueprint, jsonify, make_response, render_template, request

from oap.smi import intelligence_capability_registry, sovereign_controls

from . import agents as agent_registry
from . import (
    ai_behaviour,
    autonomy_levels,
    esim_provisioning,
    esim_runtime,
    provider_fabric,
    web_security,
)

bp = Blueprint("provider_fabric", __name__, template_folder="templates")
_LOGGER = logging.getLogger(__name__)
if not _LOGGER.handlers:
    _handler = logging.StreamHandler()
    _handler.setFormatter(logging.Formatter("%(message)s"))
    _LOGGER.addHandler(_handler)
_LOGGER.setLevel(logging.INFO)
_LOGGER.propagate = False
_ESIM_BOOT_STATUS = esim_runtime.configure()
_LOGGER.info(
    "%s",
    json.dumps(
        {
            "event": "oap_esim_runtime_attestation",
            "persistence_attached": _ESIM_BOOT_STATUS.get("persistence_attached") is True,
            "database_configured": _ESIM_BOOT_STATUS.get("database_configured") is True,
            "schema_ready": _ESIM_BOOT_STATUS.get("schema_ready") is True,
            "reason": str(_ESIM_BOOT_STATUS.get("reason") or "unknown"),
        },
        separators=(",", ":"),
        sort_keys=True,
    ),
)


def _no_store(response):
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


def _esim_response(payload: dict, status: int = 200):
    return _no_store(make_response(jsonify(payload), status))


def _esim_error(exc: Exception):
    code = str(exc) or type(exc).__name__
    if isinstance(exc, KeyError):
        return _esim_response({"error": {"code": "esim_request_not_found"}}, 404)
    if isinstance(exc, PermissionError):
        return _esim_response({"error": {"code": code}}, 403)
    if isinstance(exc, ValueError):
        return _esim_response({"error": {"code": code}}, 400)
    if isinstance(exc, RuntimeError):
        return _esim_response({"error": {"code": code}}, 503)
    return _esim_response({"error": {"code": "esim_unavailable"}}, 503)


def _esim_runtime_guard():
    status = esim_runtime.configure()
    if status.get("persistence_attached") is not True:
        return _esim_response(
            {"error": {"code": status.get("reason", "esim_runtime_unavailable")}},
            503,
        )
    return None


def _esim_write_guard():
    if guard := _esim_runtime_guard():
        return guard
    if not web_security.csrf_valid(request):
        return _esim_response({"error": {"code": "csrf_failed"}}, 403)
    return None


@bp.get("/providers")
@web_security.login_required()
def provider_dashboard():
    response = make_response(
        render_template(
            "provider_fabric.html",
            fabric=provider_fabric.get_private_provider_fabric(),
        )
    )
    return _no_store(response)


@bp.get("/providers/status")
@web_security.login_required(api=True)
def provider_status():
    return _no_store(make_response(jsonify(provider_fabric.get_coarse_provider_status())))


@bp.get("/esim/status")
@web_security.login_required(api=True, founder_only=True)
def esim_status():
    return _esim_response({"esim_runtime": esim_runtime.configure()})


@bp.post("/esim/requests")
@web_security.login_required(api=True, founder_only=True)
def esim_create_request():
    if guard := _esim_write_guard():
        return guard
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return _esim_response({"error": {"code": "json_object_required"}}, 400)
    try:
        item = esim_provisioning.CORE.request(
            subject_id=web_security.authenticated_identity(),
            purpose=body.get("purpose"),
        )
        return _esim_response({"esim_request": item}, 201)
    except Exception as exc:  # noqa: BLE001
        return _esim_error(exc)


@bp.get("/esim/requests/<request_id>")
@web_security.login_required(api=True, founder_only=True)
def esim_get_request(request_id: str):
    if guard := _esim_runtime_guard():
        return guard
    try:
        return _esim_response({"esim_request": esim_provisioning.CORE.get(request_id)})
    except Exception as exc:  # noqa: BLE001
        return _esim_error(exc)


@bp.get("/esim/requests/<request_id>/events")
@web_security.login_required(api=True, founder_only=True)
def esim_get_events(request_id: str):
    if guard := _esim_runtime_guard():
        return guard
    try:
        return _esim_response({"events": esim_provisioning.CORE.events(request_id)})
    except Exception as exc:  # noqa: BLE001
        return _esim_error(exc)


def _esim_action(request_id: str, action: str):
    if guard := _esim_write_guard():
        return guard
    try:
        core = esim_provisioning.CORE
        if action == "approve":
            item = core.approve(
                request_id,
                founder_identity=web_security.authenticated_identity(),
            )
        else:
            item = getattr(core, action)(request_id)
        return _esim_response({"esim_request": item})
    except Exception as exc:  # noqa: BLE001
        return _esim_error(exc)


@bp.post("/esim/requests/<request_id>/approve")
@web_security.login_required(api=True, founder_only=True)
def esim_approve(request_id: str):
    return _esim_action(request_id, "approve")


@bp.post("/esim/requests/<request_id>/provision")
@web_security.login_required(api=True, founder_only=True)
def esim_provision(request_id: str):
    return _esim_action(request_id, "provision")


@bp.post("/esim/requests/<request_id>/suspend")
@web_security.login_required(api=True, founder_only=True)
def esim_suspend(request_id: str):
    return _esim_action(request_id, "suspend")


@bp.post("/esim/requests/<request_id>/resume")
@web_security.login_required(api=True, founder_only=True)
def esim_resume(request_id: str):
    return _esim_action(request_id, "resume")


@bp.post("/esim/requests/<request_id>/revoke")
@web_security.login_required(api=True, founder_only=True)
def esim_revoke(request_id: str):
    return _esim_action(request_id, "revoke")


@bp.get("/alignment")
@web_security.login_required(founder_only=True)
def alignment_dashboard():
    sovereignty = sovereign_controls.SovereignControlPlane().status()
    capability_registry = intelligence_capability_registry.status(
        agent_registry.LOCKED_WORLD_IDS
    )
    autonomy = autonomy_levels.status()
    behaviour = ai_behaviour.status()
    response = make_response(
        render_template(
            "alignment_sovereignty.html",
            sovereignty=sovereignty,
            capability_registry=capability_registry,
            autonomy=autonomy,
            behaviour=behaviour,
            worlds=agent_registry.INTELLIGENCE_WORLDS,
            agent_count=agent_registry.LOCKED_AGENT_COUNT,
        )
    )
    return _no_store(response)


@bp.get("/alignment/status")
@web_security.login_required(api=True, founder_only=True)
def alignment_status():
    sovereignty = sovereign_controls.SovereignControlPlane().status()
    capability_registry = intelligence_capability_registry.status(
        agent_registry.LOCKED_WORLD_IDS
    )
    autonomy = autonomy_levels.status()
    behaviour = ai_behaviour.status()
    return _no_store(
        make_response(
            jsonify(
                single_smi_brain=True,
                world_count=len(agent_registry.INTELLIGENCE_WORLDS),
                agent_count=agent_registry.LOCKED_AGENT_COUNT,
                capability_count=capability_registry["capability_count"],
                capability_alignment=capability_registry["validation"]["passed"],
                autonomy=autonomy,
                ai_behaviour=behaviour,
                sovereignty=sovereignty,
                provider_authority=False,
                human_authority_final=True,
            )
        )
    )
