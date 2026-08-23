"""Read-only Flask routes for the Mission Control vertical slice."""

from __future__ import annotations

from flask import Blueprint, jsonify, make_response, render_template, request

from . import agents as agent_registry
from . import brain, infrastructure, linkup, ollama_chat, organism, status, war_room

ALLOWED_MODES = ("sovereign", "mission", "approval")

bp = Blueprint(
    "mission_control",
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="/static",
)


def _no_store(response):
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


@bp.get("/")
@bp.get("")
def mission_workspace():
    """Render the non-operational Mission Control workspace."""

    mode = request.args.get("mode", "sovereign").strip().lower()
    if mode not in ALLOWED_MODES:
        return _no_store(
            make_response(
                jsonify(
                    error={
                        "code": "invalid_mode",
                        "message": "Unsupported Mission Control mode.",
                        "allowed_modes": list(ALLOWED_MODES),
                    }
                ),
                400,
            )
        )

    response = make_response(
        render_template(
            "mission.html",
            active_mode=mode,
            allowed_modes=ALLOWED_MODES,
            gateway=status.get_public_gateway_status(),
        )
    )
    return _no_store(response)


@bp.get("/agents")
def agent_intelligence():
    """Render the OAP-owned Agent Intelligence directory without actions."""

    requested_family = request.args.get("family", "").strip().lower()
    family_id = requested_family or None
    if family_id is not None and family_id not in agent_registry.LOCKED_FAMILY_IDS:
        return _no_store(
            make_response(
                jsonify(
                    error={
                        "code": "invalid_intelligence_family",
                        "message": "Unsupported OAP Intelligence family.",
                        "allowed_families": list(agent_registry.LOCKED_FAMILY_IDS),
                    }
                ),
                400,
            )
        )

    query = request.args.get("q", "")
    response = make_response(
        render_template(
            "agents.html",
            directory=agent_registry.get_public_agent_directory(family_id, query),
        )
    )
    return _no_store(response)


@bp.get("/brain")
def brain_dashboard():
    """Render SMI implementation readiness without running a signal."""

    response = make_response(
        render_template(
            "brain.html",
            brain=brain.get_public_brain_status(),
        )
    )
    return _no_store(response)


@bp.get("/brain/status")
def brain_status():
    """Return a coarse, read-only SMI implementation projection."""

    return _no_store(make_response(jsonify(brain.get_public_brain_status())))


@bp.get("/ollama")
def ollama_chat_dashboard():
    """Render the local-provider chat shell without contacting the provider."""

    response = make_response(
        render_template(
            "ollama_chat.html",
            chat=ollama_chat.get_public_ollama_chat(),
        )
    )
    return _no_store(response)


@bp.get("/war-room")
def war_room_dashboard():
    """Render consequence-review readiness without running a simulation."""

    response = make_response(
        render_template(
            "war_room.html",
            war_room=war_room.get_public_war_room(),
        )
    )
    return _no_store(response)


@bp.get("/war-room/status")
def war_room_status():
    """Return a coarse, redacted War Room readiness projection."""

    return _no_store(make_response(jsonify(war_room.get_public_war_room())))


@bp.get("/infrastructure")
def infrastructure_dashboard():
    """Render locked Infrastructure awareness without provider operations."""

    response = make_response(
        render_template(
            "infrastructure.html",
            infrastructure=infrastructure.get_public_infrastructure(),
            shared_health=status.get_public_gateway_status()["components"],
        )
    )
    return _no_store(response)


@bp.get("/linkup")
def link_dashboard():
    """Render The Link without identities, conversations or send controls."""

    response = make_response(
        render_template(
            "linkup.html",
            link=linkup.get_public_link_dashboard(),
        )
    )
    return _no_store(response)


@bp.get("/organism")
def organism_anatomy():
    """Render the canonical architecture without exposing operational controls."""

    response = make_response(
        render_template(
            "organism.html",
            anatomy=organism.get_public_anatomy(),
        )
    )
    return _no_store(response)


@bp.get("/status")
def mission_status():
    """Return public status only; privileged status remains fail-closed."""

    scope = request.args.get("scope", "public").strip().lower()
    if scope != "public":
        return _no_store(
            make_response(
                jsonify(
                    error={
                        "code": "authentication_required",
                        "message": (
                            "Privileged Mission Control status is unavailable "
                            "until Identity and Permission checks are enabled."
                        ),
                    }
                ),
                403,
            )
        )

    return _no_store(make_response(jsonify(status.get_public_gateway_status())))
