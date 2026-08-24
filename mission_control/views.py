"""Public product routes and authenticated Mission Control routes."""

from __future__ import annotations

import json

from flask import (
    Blueprint,
    Response,
    jsonify,
    make_response,
    redirect,
    render_template,
    request,
    stream_with_context,
    url_for,
)

from . import agents as agent_registry
from . import (
    approval_service,
    authority,
    brain,
    infrastructure,
    judgement,
    ollama_chat,
    organism,
    postgres_db,
    products,
    public_store,
    smi_chat_runtime,
    status,
    web_security,
)

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


def _error(code: str, message: str, status_code: int):
    return _no_store(
        make_response(jsonify(error={"code": code, "message": message}), status_code)
    )


def _chat_identity() -> str:
    return web_security.authenticated_identity()


def _chat_rate_allowed(identity_id: str) -> bool:
    return web_security.CHAT_BURST_LIMITER.allow(identity_id)


@bp.get("/")
@bp.get("")
@web_security.login_required()
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
@web_security.login_required()
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
@web_security.login_required()
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
@web_security.login_required(api=True)
def brain_status():
    """Return a coarse, read-only SMI implementation projection."""

    return _no_store(make_response(jsonify(brain.get_public_brain_status())))


def _sync_private_identity() -> tuple[dict[str, object], dict[str, object]]:
    """Ensure the verified Neon UUID has its canonical OAP role binding."""

    user = web_security.current_authenticated_user()
    if user is None:  # pragma: no cover - decorator is the fail-closed gate.
        raise PermissionError("authentication_required")
    public_store.ensure_authenticated_user(
        str(user["id"]),
        email=str(user["email"]),
        display_name=str(user["name"]),
        email_verified=bool(user.get("email_verified")),
    )
    with postgres_db.connect(readonly=True) as connection:
        record = authority.authority_record(connection, str(user["id"]))
    return user, record or {"is_human_authority": False, "authority_level": 5}


@bp.get("/judgement")
@web_security.login_required()
def judgement_dashboard():
    """Render the five automated sections and sixth human decision gate."""

    try:
        user, authority_record = _sync_private_identity()
        reviews = judgement.list_reviews(
            None if authority_record["is_human_authority"] else str(user["id"])
        )
    except (public_store.PublicStoreUnavailable, RuntimeError):
        return _error(
            "judgement_unavailable",
            "The governed decision ledger is temporarily unavailable.",
            503,
        )
    response = make_response(
        render_template(
            "judgement.html",
            reviews=reviews,
            authority=authority_record,
            judgement_status=judgement.status(),
            approval_status=approval_service.status(),
        )
    )
    return _no_store(response)


@bp.post("/judgement/<request_id>/decision")
@web_security.login_required(api=True)
def judgement_decision(request_id: str):
    """Record one signed level-zero decision; never execute the recommendation."""

    if not web_security.csrf_valid(request):
        return _error(
            "csrf_failed",
            "The secure session expired. Refresh the page and try again.",
            403,
        )
    try:
        user, _authority_record = _sync_private_identity()
        approval_service.record_decision(
            request_id=request_id,
            identity_id=str(user["id"]),
            decision=request.form.get("decision")
            or (request.get_json(silent=True) or {}).get("decision"),
        )
    except authority.HumanAuthorityRequired:
        return _error(
            "human_authority_required",
            "Only active level-zero Human Authority may record this decision.",
            403,
        )
    except ValueError as exc:
        return _error("invalid_decision", str(exc), 400)
    except (approval_service.ApprovalUnavailable, public_store.PublicStoreUnavailable):
        return _error(
            "approval_unavailable",
            "The signed approval receipt could not be recorded safely.",
            503,
        )
    if request.is_json:
        return _no_store(
            make_response(
                jsonify(
                    status="recorded",
                    request_id=request_id,
                    execution_granted=False,
                )
            )
        )
    return _no_store(make_response(redirect(url_for("mission_control.judgement_dashboard"))))


@bp.get("/ollama")
@web_security.login_required()
def ollama_chat_dashboard():
    """Render the local-provider chat shell without contacting the provider."""

    _chat_identity()
    response = make_response(
        render_template(
            "ollama_chat.html",
            chat=ollama_chat.get_public_ollama_chat(),
        )
    )
    return _no_store(response)


@bp.post("/chat")
@web_security.login_required(api=True)
def smi_chat_message():
    """Process one governed recommendation request and persist it in HRM."""
    if not web_security.csrf_valid(request):
        return _error(
            "csrf_failed",
            "The secure session expired. Refresh the page and try again.",
            403,
        )
    payload = request.get_json(silent=True) or {}
    if not isinstance(payload, dict):
        return _error("invalid_request", "A JSON object is required.", 400)
    identity_id = _chat_identity()
    if not _chat_rate_allowed(identity_id):
        response = _error(
            "rate_limited", "Too many SMI requests. Wait one minute and try again.", 429
        )
        response.headers["Retry-After"] = "60"
        return response
    try:
        result = smi_chat_runtime.chat(
            payload.get("message"),
            identity_id,
            payload.get("display_name", "OAP Member"),
            payload.get("conversation_id"),
            payload.get("image_data"),
            payload.get("attachment"),
            code_mode=bool(payload.get("code_mode")),
        )
        return _no_store(make_response(jsonify(result)))
    except (TypeError, ValueError) as exc:
        if str(exc) == "chat_rate_limit":
            response = _error(
                "rate_limited",
                "Too many SMI requests. Wait one minute and try again.",
                429,
            )
            response.headers["Retry-After"] = "60"
            return response
        return _error("invalid_request", str(exc), 400)
    except PermissionError:
        return _error(
            "permission_denied", "REQUEST_RECOMMENDATION permission required", 403
        )
    except RuntimeError:
        return _error(
            "provider_unavailable",
            "SMI provider is temporarily unavailable.",
            503,
        )


@bp.post("/chat/stream")
@web_security.login_required(api=True)
def smi_chat_stream():
    """Stream genuine provider deltas, then confirm governed persistence."""

    if not web_security.csrf_valid(request):
        return _error(
            "csrf_failed",
            "The secure session expired. Refresh the page and try again.",
            403,
        )
    payload = request.get_json(silent=True) or {}
    if not isinstance(payload, dict):
        return _error("invalid_request", "A JSON object is required.", 400)
    identity_id = _chat_identity()
    if not _chat_rate_allowed(identity_id):
        response = _error(
            "rate_limited", "Too many SMI requests. Wait one minute and try again.", 429
        )
        response.headers["Retry-After"] = "60"
        return response

    def generate():
        events = smi_chat_runtime.chat_events(
            payload.get("message"),
            identity_id,
            payload.get("display_name", "OAP Member"),
            payload.get("conversation_id"),
            payload.get("image_data"),
            payload.get("attachment"),
            code_mode=bool(payload.get("code_mode")),
        )
        for item in events:
            event_name = str(item.get("type", "message"))
            data = {key: value for key, value in item.items() if key != "type"}
            yield (
                f"event: {event_name}\n"
                f"data: {json.dumps(data, ensure_ascii=False, separators=(',', ':'))}\n\n"
            )

    response = Response(stream_with_context(generate()), mimetype="text/event-stream")
    response.headers["Cache-Control"] = "no-store, no-transform"
    response.headers["X-Accel-Buffering"] = "no"
    response.headers["Connection"] = "keep-alive"
    return response


@bp.get("/conversations")
@web_security.login_required(api=True)
def smi_conversations():
    """List only the current signed-session identity's SMI conversations."""

    try:
        conversations = smi_chat_runtime.list_conversations(_chat_identity())
        return _no_store(make_response(jsonify(conversations=conversations)))
    except RuntimeError:
        return _error(
            "conversation_store_unavailable",
            "Conversation history is temporarily unavailable.",
            503,
        )


@bp.get("/conversations/<conversation_id>")
@web_security.login_required(api=True)
def smi_conversation(conversation_id: str):
    """Load one owned conversation without exposing another identity's data."""

    try:
        conversation = smi_chat_runtime.get_conversation(
            _chat_identity(), conversation_id
        )
        return _no_store(make_response(jsonify(conversation)))
    except ValueError:
        return _error("invalid_conversation", "Conversation not found.", 404)
    except RuntimeError:
        return _error(
            "conversation_store_unavailable",
            "Conversation history is temporarily unavailable.",
            503,
        )


@bp.delete("/conversations/<conversation_id>")
@web_security.login_required(api=True)
def delete_smi_conversation(conversation_id: str):
    """Delete one owned conversation after an explicit CSRF-protected action."""

    if not web_security.csrf_valid(request):
        return _error(
            "csrf_failed",
            "The secure session expired. Refresh the page and try again.",
            403,
        )
    try:
        result = smi_chat_runtime.delete_conversation(
            _chat_identity(), conversation_id
        )
        return _no_store(make_response(jsonify(result)))
    except ValueError:
        return _error("invalid_conversation", "Conversation not found.", 404)
    except RuntimeError:
        return _error(
            "conversation_store_unavailable",
            "Conversation history is temporarily unavailable.",
            503,
        )


@bp.get("/chat/status")
@web_security.login_required(api=True)
def smi_chat_health():
    """Return detailed intelligence health only to a signed-in member."""
    return _no_store(make_response(jsonify(smi_chat_runtime.health())))


@bp.get("/infrastructure")
@web_security.login_required()
def infrastructure_dashboard():
    """Render locked Infrastructure awareness without provider operations."""

    response = make_response(
        render_template(
            "mission_control/infrastructure.html",
            infrastructure=infrastructure.get_public_infrastructure(),
            shared_health=status.get_public_gateway_status()["components"],
        )
    )
    return _no_store(response)


@bp.get("/spot")
def spot_dashboard():
    """Keep the former product address as a public compatibility redirect."""

    return _no_store(make_response(redirect(url_for("the_spot_front_door"))))


@bp.get("/spot/<capability_id>")
def spot_capability(capability_id: str):
    """Keep former capability addresses as compatibility redirects."""

    capability_slug = products.get_public_spot_slug(capability_id)
    if capability_slug is None:
        capability_slug = "unavailable"
    return _no_store(
        make_response(
            redirect(
                url_for(
                    "spot_capability_front_door", capability_slug=capability_slug
                )
            )
        )
    )


@bp.get("/the-link")
def the_link_dashboard():
    """Keep the former Link address as a public compatibility redirect."""

    return _no_store(make_response(redirect(url_for("the_link_front_door"))))


@bp.get("/linkup")
def link_dashboard():
    """Keep the former LinkUp address as a public compatibility redirect."""

    return _no_store(make_response(redirect(url_for("linkup_front_door"))))


@bp.get("/organism")
@web_security.login_required()
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
@web_security.login_required(api=True)
def mission_status():
    """Return the internal status projection only after sign-in."""

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
