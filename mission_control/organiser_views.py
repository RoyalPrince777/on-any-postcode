"""Founder-only SMI Organiser and connectivity-brief review surfaces."""
from __future__ import annotations

from uuid import uuid4

from flask import (
    Blueprint,
    jsonify,
    make_response,
    redirect,
    render_template,
    request,
    url_for,
)

from . import (
    connectivity_briefs,
    organiser_schedules,
    public_store,
    smi_archive,
    web_security,
    workspaces,
)

bp = Blueprint("smi_organiser", __name__)


def _no_store(response):
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


def _owner() -> tuple[str, dict[str, object]]:
    user = web_security.current_authenticated_user()
    if not isinstance(user, dict):
        raise PermissionError("authentication_required")
    return str(user["id"]), user


def _read(owner_id: str):
    schedules = organiser_schedules.list_all(owner_id)
    briefs = connectivity_briefs.list_all(owner_id)
    return schedules, briefs


def _page(*, error: str = "", form: dict[str, object] | None = None, status: int = 200):
    owner_id, _user = _owner()
    schedules: tuple[dict[str, object], ...] = ()
    briefs: tuple[dict[str, object], ...] = ()
    store_error = ""
    try:
        schedules, briefs = _read(owner_id)
    except (
        organiser_schedules.ScheduleMirrorUnavailable,
        connectivity_briefs.ConnectivityBriefUnavailable,
        workspaces.WorkspaceUnavailable,
    ) as exc:
        store_error = str(exc)
    response = make_response(
        render_template(
            "organiser.html",
            schedules=schedules,
            briefs=briefs,
            archive=smi_archive.status(),
            error=error or store_error,
            form=form or {},
            imported=request.args.get("imported", ""),
            oap_csrf_token=web_security.csrf_token(),
        ),
        status,
    )
    return _no_store(response)


@bp.get("/organiser")
@web_security.login_required(founder_only=True)
def dashboard():
    return _page()


@bp.post("/organiser/connectivity-briefs")
@web_security.login_required(founder_only=True)
def import_connectivity_brief():
    if not web_security.csrf_valid(request):
        return _page(error="csrf_failed", form=dict(request.form), status=403)
    owner_id, user = _owner()
    links = tuple(
        line.strip()
        for line in str(request.form.get("evidence_links") or "").splitlines()
        if line.strip()
    )
    form = dict(request.form)
    try:
        public_store.ensure_authenticated_user(
            owner_id,
            email=str(user.get("email") or ""),
            display_name=str(user.get("name") or "Founder"),
            email_verified=bool(user.get("email_verified")),
            store_email=False,
        )
        brief = connectivity_briefs.ConnectivityBrief(
            brief_id=str(request.form.get("brief_id") or uuid4()),
            source_run_id=str(request.form.get("source_run_id") or ""),
            title=str(request.form.get("title") or ""),
            completed_at=str(request.form.get("completed_at") or ""),
            summary=str(request.form.get("summary") or ""),
            evidence_links=links,
            evidence_score=int(request.form.get("evidence_score") or -1),
            decision=str(request.form.get("decision") or "pending_review"),
            no_material_update=request.form.get("no_material_update") == "on",
        )
        connectivity_briefs.upsert(owner_id, brief)
    except (
        TypeError,
        ValueError,
        PermissionError,
        connectivity_briefs.ConnectivityBriefUnavailable,
        workspaces.WorkspaceUnavailable,
        public_store.PublicStoreUnavailable,
    ) as exc:
        return _page(error=str(exc), form=form, status=400)
    return redirect(url_for("smi_organiser.dashboard", imported=brief.brief_id))


@bp.post("/organiser/agents-hq/chat")
@web_security.login_required(api=True, founder_only=True)
def founder_agents_hq_chat():
    """Authenticated Founder -> governed SMI exchange, not agent impersonation."""
    from .smi_agents_hq_turns import founder_council_chat

    if not web_security.csrf_valid(request):
        return _no_store(make_response(jsonify({"error": "csrf_failed"}), 403))
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return _no_store(make_response(jsonify({"error": "invalid_request"}), 400))
    owner_id, user = _owner()
    try:
        result = founder_council_chat(
            message=payload.get("message"),
            identity_id=owner_id,
            display_name=str(user.get("name") or "Founder"),
            founder_authenticated=True,
            conversation_id=payload.get("conversation_id"),
        )
    except (TypeError, ValueError):
        return _no_store(make_response(jsonify({"error": "invalid_request"}), 400))
    except PermissionError:
        return _no_store(make_response(jsonify({"error": "permission_denied"}), 403))
    except RuntimeError:
        return _no_store(make_response(jsonify({"error": "provider_unavailable"}), 503))
    return _no_store(make_response(jsonify(result)))


@bp.post("/organiser/agents-hq/select")
@web_security.login_required(api=True, founder_only=True)
def founder_agents_hq_select():
    """Advise on eligible mission specialists; do not create workers or grant access."""
    from oap.smi.alliance_selection import select_passport_verified_alliance

    if not web_security.csrf_valid(request):
        return _no_store(make_response(jsonify({"error": "csrf_failed"}), 403))
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return _no_store(make_response(jsonify({"error": "invalid_request"}), 400))
    mission = payload.get("mission")
    task_type = payload.get("task_type", "GENERAL")
    if (
        not isinstance(mission, str)
        or not mission.strip()
        or len(mission) > 2000
        or not isinstance(task_type, str)
        or task_type.upper() not in {"GENERAL", "TECHNICAL", "STRATEGY", "MONITORING", "COMMUNITY", "CULTURE"}
    ):
        return _no_store(make_response(jsonify({"error": "invalid_mission"}), 400))
    result = select_passport_verified_alliance(
        task_type.upper(), mission, high_impact=payload.get("high_impact") is True,
        distributed_work=payload.get("distributed_work") is True,
    )
    return _no_store(make_response(jsonify({
        "capabilities": result.capabilities,
        "recommended_specialists": result.specialists,
        "unassigned_capabilities": result.unassigned_capabilities,
        "excluded_unregistered": result.excluded_unregistered,
        "excluded_inactive": result.excluded_inactive,
        "advisory_only": True, "agent_messages_generated": False,
        "execution_authorised": False, "founder_final": True,
    })))


@bp.get("/organiser/agents-hq/conversation/<conversation_id>")
@web_security.login_required(api=True, founder_only=True)
def founder_agents_hq_conversation(conversation_id: str):
    """Read back persisted messages through the existing owner-scoped SMI store."""
    from .smi_chat_runtime import get_conversation

    owner_id, _user = _owner()
    try:
        result = get_conversation(owner_id, conversation_id)
    except ValueError:
        return _no_store(make_response(jsonify({"error": "conversation_not_found"}), 404))
    except RuntimeError:
        return _no_store(make_response(jsonify({"error": "conversation_store_unavailable"}), 503))
    return _no_store(make_response(jsonify({
        "conversation": result,
        "source": "existing_owner_scoped_smi_store",
        "individual_agent_sender_verified": False,
        "agent_to_agent_delivery_proven": False,
        "founder_final": True,
    })))
