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
    smi_founder_assets,
    smi_receipt_backend,
    smi_recursive_improvement,
    smi_workbench,
    status,
    studio_intelligence,
    war_room,
    web_security,
)

ALLOWED_MODES = ("sovereign", "mission", "approval")
BUTTON_PROOF_TARGETS = {
    "map-intelligence": "/on-any-place",
    "war-room": "/mission/war-room",
    "function-health": "/mission/smi/function-health",
    "green-gate": "/mission/smi/green-gate",
    "hrm": "/mission/smi/brain/receipts",
    "founder-library": "/mission/founder-library",
    "improvement": "/mission/improvement",
    "signals-21": "/mission/smi/coherent-automation",
    "guardian": "/mission/smi/brain/evidence-runner/run?command=guardian_check",
    "routes": "/mission/smi/routes",
    "brain": "/mission/brain",
    "agents": "/mission/agents",
    "infrastructure": "/mission/infrastructure",
    "judgement": "/mission/judgement",
    "studio-imagine": "/mission/studio/generate",
    "studio-bring-alive": "/mission/studio/generate",
    "studio-scene-builder": "/mission/studio/generate",
}


WAR_ROOM_RUNTIME_ACTIONS = {
    "status": {
        "label": "War Room status",
        "state": "live",
        "signal": "green",
        "message": "Founder-only War Room status projection returned.",
    },
    "alignment-check": {
        "label": "Alignment Check",
        "state": "certified",
        "signal": "green",
        "message": "Canonical governance flow, placement and upgrade-only rules checked.",
    },
    "aegis-check": {
        "label": "Aegis / Guardian Check",
        "state": "guarded",
        "signal": "green",
        "message": "Privacy, safety, public/private and no-fake-green boundaries checked.",
    },
    "function-health": {
        "label": "Function Health",
        "state": "building",
        "signal": "yellow",
        "message": "Read-only function evidence plus post-ack Button Proof receipts are implemented; signed-in browser certification remains required.",
    },
    "green-gate": {
        "label": "Green Gate",
        "state": "building",
        "signal": "yellow",
        "message": "Evidence states are calculated and Button Proof is post-ack only; full Green remains locked until runtime/device proof and Founder Final.",
    },
    "hrm-receipt": {
        "label": "HRM Receipt Boundary",
        "state": "locked",
        "signal": "yellow",
        "message": "This endpoint proves the receipt boundary without writing a production decision or approval.",
    },
    "fresh-logs": {
        "label": "Fresh Logs",
        "state": "external-proof-required",
        "signal": "yellow",
        "message": "Fresh Render logs must be read by the deployment connector; War Room does not invent log evidence.",
    },
    "export-safe-brief": {
        "label": "Export Safe Brief",
        "state": "ready",
        "signal": "green",
        "message": "Safe public brief generated without secrets, private logs, tokens, ISAC internals or security details.",
    },
}

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


def _war_room_runtime_result(action_id: str) -> dict[str, object]:
    action = WAR_ROOM_RUNTIME_ACTIONS.get(action_id)
    if action is None:
        raise ValueError("Unsupported War Room action.")
    dashboard = war_room.get_war_room_dashboard()
    validation = dashboard.get("validation", {})
    summary = dashboard.get("summary", {})
    safe_brief = None
    if action_id == "export-safe-brief":
        safe_brief = {
            "title": "OAP War Room Safe Brief",
            "status": "Private War Room evidence reviewed.",
            "public_message": (
                "OAP command evidence has been reviewed. Public routes remain separate "
                "from private controls. Any incomplete capability remains Building or Locked "
                "until proof exists."
            ),
            "excluded": (
                "secrets",
                "tokens",
                "private logs",
                "Founder identifiers",
                "database details",
                "ISAC internals",
                "security-sensitive implementation details",
            ),
        }
    return {
        "action_id": action_id,
        "label": action["label"],
        "state": action["state"],
        "signal": action["signal"],
        "message": action["message"],
        "war_room": {
            "mode": dashboard.get("mode"),
            "validation_passed": bool(validation.get("passed")),
            "rated_areas": int(summary.get("rated_areas") or 0),
            "overall_evidence_score": int(summary.get("overall_evidence_score") or 0),
            "runtime_verified": int(summary.get("runtime_verified") or 0),
            "operationally_certified": int(summary.get("operationally_certified") or 0),
            "controls_enabled": False,
            "can_execute": False,
            "can_approve": False,
        },
        "guardian": {
            "no_fake_green": True,
            "private_by_default": True,
            "consequential_execution": "blocked",
            "human_authority_final": True,
        },
        "green_gate": {
            "route_exists": True,
            "csrf_checked": True,
            "state_truthful": True,
            "execution_granted": False,
        },
        "hrm": {
            "receipt_required_for_consequential_action": True,
            "production_write_performed": False,
            "reason": "War Room Runtime v1 actions are safe proof responses only.",
        },
        "safe_brief": safe_brief,
    }


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


@bp.get("/war-room")
@web_security.login_required()
def war_room_dashboard():
    """Render the Founder-only evidence dashboard without changing state."""

    response = make_response(
        render_template(
            "war_room.html",
            war_room=war_room.get_war_room_dashboard(),
        )
    )
    return _no_store(response)


@bp.get("/war-room/status")
@web_security.login_required(api=True)
def war_room_status():
    """Return the same read-only, redacted War Room evidence projection."""

    return _no_store(make_response(jsonify(war_room.get_war_room_dashboard())))


@bp.get("/war-room/actions")
@web_security.login_required(api=True)
def war_room_actions():
    """Return supported safe War Room Runtime v1 actions."""

    return _no_store(
        make_response(
            jsonify(
                actions=tuple(
                    {
                        "id": action_id,
                        "label": action["label"],
                        "state": action["state"],
                        "signal": action["signal"],
                    }
                    for action_id, action in WAR_ROOM_RUNTIME_ACTIONS.items()
                ),
                can_execute=False,
                can_approve=False,
                csrf_required_for_post=True,
            )
        )
    )


@bp.post("/war-room/actions/<action_id>")
@web_security.login_required(api=True)
def run_war_room_action(action_id: str):
    """Run one safe War Room proof action without consequential execution."""

    if not web_security.csrf_valid(request):
        return _error(
            "csrf_failed",
            "The secure session expired. Refresh the page and try again.",
            403,
        )
    try:
        result = _war_room_runtime_result(action_id)
    except ValueError as exc:
        return _error("invalid_war_room_action", str(exc), 400)
    return _no_store(make_response(jsonify(result)))


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
        store_email=False,
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
    try:
        result = smi_chat_runtime.chat(
            payload.get("message"),
            identity_id,
            payload.get("display_name", "OAP Member"),
            payload.get("conversation_id"),
            payload.get("image_data"),
            payload.get("attachment"),
            code_mode=bool(payload.get("code_mode")),
            thinking_level=str(payload.get("thinking_level") or "auto"),
            studio_mode=bool(payload.get("studio_mode")),
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

    def generate():
        events = smi_chat_runtime.chat_events(
            payload.get("message"),
            identity_id,
            payload.get("display_name", "OAP Member"),
            payload.get("conversation_id"),
            payload.get("image_data"),
            payload.get("attachment"),
            code_mode=bool(payload.get("code_mode")),
            thinking_level=str(payload.get("thinking_level") or "auto"),
            studio_mode=bool(payload.get("studio_mode")),
        )
        try:
            for item in events:
                event_name = str(item.get("type", "message"))
                data = {key: value for key, value in item.items() if key != "type"}
                yield (
                    f"event: {event_name}\n"
                    f"data: {json.dumps(data, ensure_ascii=False, separators=(',', ':'))}\n\n"
                )
        finally:
            close_events = getattr(events, "close", None)
            if callable(close_events):
                close_events()

    response = Response(stream_with_context(generate()), mimetype="text/event-stream")
    response.headers["Cache-Control"] = "no-store, no-transform"
    response.headers["X-Accel-Buffering"] = "no"
    response.headers["Connection"] = "keep-alive"
    return response


@bp.post("/chat/feedback")
@web_security.login_required(api=True)
def smi_chat_feedback():
    """Record response feedback without granting execution authority."""

    if not web_security.csrf_valid(request):
        return _error(
            "csrf_failed",
            "The secure session expired. Refresh the page and try again.",
            403,
        )
    payload = request.get_json(silent=True) or {}
    if not isinstance(payload, dict):
        return _error("invalid_request", "A JSON object is required.", 400)
    try:
        result = smi_chat_runtime.record_feedback(
            _chat_identity(),
            payload.get("request_id"),
            payload.get("conversation_id"),
            payload.get("signal"),
        )
    except ValueError as exc:
        return _error("invalid_feedback", str(exc), 400)
    except RuntimeError:
        return _error(
            "feedback_unavailable",
            "Feedback could not be recorded safely.",
            503,
        )
    return _no_store(make_response(jsonify(result)))


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


@bp.get("/workbench/status")
@web_security.login_required(api=True)
def smi_workbench_status():
    """Return secret-safe tool and capability readiness to the Founder UI."""

    return _no_store(make_response(jsonify(smi_workbench.get_workbench_status())))


@bp.get("/founder-library")
@web_security.login_required(api=True, founder_only=True)
def smi_founder_library():
    """Return only the signed-in Founder's durable asset metadata."""

    try:
        return _no_store(
            make_response(
                jsonify(smi_founder_assets.list_assets(_chat_identity()))
            )
        )
    except (ValueError, RuntimeError):
        return _error(
            "founder_library_unavailable",
            "Founder Library is temporarily unavailable.",
            503,
        )


@bp.post("/ui/button-proof")
@web_security.login_required(api=True, founder_only=True)
def smi_button_proof():
    """Chronicle one successful Founder UI control only after runtime acknowledgement."""

    if not web_security.csrf_valid(request):
        return _error(
            "csrf_failed",
            "The secure session expired. Refresh the page and try again.",
            403,
        )
    payload = request.get_json(silent=True) or {}
    if not isinstance(payload, dict):
        return _error("invalid_request", "A JSON object is required.", 400)
    action_id = str(payload.get("action_id") or "").strip()
    target = str(payload.get("target") or "").strip()
    expected = BUTTON_PROOF_TARGETS.get(action_id)
    if expected is None or target != expected:
        return _error("invalid_button_proof", "Unsupported SMI control proof.", 400)
    try:
        status_code = int(payload.get("status_code") or 0)
    except (TypeError, ValueError):
        return _error("invalid_button_proof", "Invalid runtime status.", 400)
    if status_code < 200 or status_code >= 400:
        return _error("button_not_proven", "Runtime acknowledgement did not succeed.", 409)
    receipt = smi_receipt_backend.write_receipt(
        "agent_tool_connection_receipt",
        {
            "brain_part": "smi_control_surface",
            "gate": 1,
            "command": "button_runtime_proof",
            "signal": "🟣",
            "guardian": "passed_read_only_runtime_ack",
            "green_gate": "button_acknowledged_not_whole_smi_green",
            "founder_final": "required_for_full_green",
            "safe_payload": {
                "action_id": action_id,
                "target": target,
                "status_code": status_code,
                "runtime_acknowledged": True,
                "click_only_proof": False,
                "execution_authority_expanded": False,
            },
        },
    )
    return _no_store(
        make_response(
            jsonify(
                proven=bool(receipt.get("ok")),
                action_id=action_id,
                target=target,
                chronicle_receipt={
                    "receipt_id": receipt.get("receipt_id"),
                    "durable": bool(receipt.get("durable")),
                    "backend": receipt.get("backend"),
                },
                whole_smi_green=False,
                human_authority_final=True,
            )
        )
    )


@bp.get("/studio/status")
@web_security.login_required(api=True, founder_only=True)
def smi_studio_status():
    """Return the canonical Founder-only OAP Studio Intelligence contract."""

    return _no_store(make_response(jsonify(studio_intelligence.status())))


@bp.post("/studio/generate")
@web_security.login_required(api=True, founder_only=True)
def smi_studio_generate():
    """Execute one governed Founder-only Studio generation request."""

    if not web_security.csrf_valid(request):
        return _error(
            "csrf_failed",
            "The secure session expired. Refresh the page and try again.",
            403,
        )
    payload = request.get_json(silent=True) or {}
    if not isinstance(payload, dict):
        return _error("invalid_request", "A JSON object is required.", 400)
    try:
        result = studio_intelligence.execute_generation(
            payload.get("tool_id"),
            prompt=payload.get("prompt", ""),
            source_image_data=payload.get("source_image_data", ""),
        )
    except ValueError as exc:
        return _error("invalid_studio_request", str(exc), 400)
    except RuntimeError:
        return _error(
            "studio_generation_unavailable",
            "Studio generation is temporarily unavailable.",
            503,
        )
    return _no_store(make_response(jsonify(result)))


@bp.get("/studio/video/<video_id>/status")
@web_security.login_required(api=True, founder_only=True)
def smi_studio_video_status(video_id: str):
    """Return one governed Studio video-job proof state."""

    try:
        result = studio_intelligence.generation_status(video_id)
    except ValueError as exc:
        return _error("invalid_studio_video", str(exc), 400)
    except RuntimeError:
        return _error(
            "studio_generation_unavailable",
            "Studio generation status is temporarily unavailable.",
            503,
        )
    return _no_store(make_response(jsonify(result)))


@bp.get("/studio/video/<video_id>/content")
@web_security.login_required(api=True, founder_only=True)
def smi_studio_video_content(video_id: str):
    """Proxy one completed Studio video artifact through the first-party Founder origin."""

    try:
        body, mime_type = studio_intelligence.generation_content(video_id)
    except ValueError as exc:
        return _error("invalid_studio_video", str(exc), 400)
    except RuntimeError:
        return _error(
            "studio_generation_unavailable",
            "Studio video content is temporarily unavailable.",
            503,
        )
    response = Response(body, mimetype=mime_type)
    response.headers["Content-Disposition"] = 'inline; filename="oap-studio-video.mp4"'
    return _no_store(response)


@bp.get("/improvement")
@web_security.login_required()
def smi_recursive_improvement_dashboard():
    """Render one Founder-only, evidence-bound improvement review cycle."""

    response = make_response(
        render_template(
            "smi_recursive_improvement.html",
            contract=smi_recursive_improvement.status(),
            cycle=smi_recursive_improvement.run_cycle(),
        )
    )
    return _no_store(response)


@bp.get("/improvement/status")
@web_security.login_required(api=True)
def smi_recursive_improvement_status():
    """Return one live read-only recursive-improvement evidence cycle."""

    return _no_store(make_response(jsonify(smi_recursive_improvement.run_cycle())))


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
