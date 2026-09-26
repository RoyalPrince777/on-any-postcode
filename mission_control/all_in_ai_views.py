"""Founder-only ALL IN A.I. Command Center surface."""

from flask import Blueprint, jsonify, make_response, request

from . import all_in_ai, all_in_ai_mission_store, all_in_ai_runtime, web_security

bp = Blueprint("all_in_ai", __name__)


def _no_store(response):
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


def _error(code: str, message: str, status_code: int):
    return _no_store(
        make_response(
            jsonify(error={"code": code, "message": message}),
            status_code,
        )
    )


def _founder_id() -> str | None:
    user = web_security.current_authenticated_user()
    if user is None:
        return None
    identity = str(user.get("id") or "").strip()
    return identity or None


def _require_csrf():
    if web_security.csrf_valid(request):
        return None
    return _error(
        "csrf_failed",
        "The secure session expired. Refresh and try again.",
        403,
    )


@bp.get("/all-in-ai")
@web_security.login_required(api=True, founder_only=True)
def all_in_ai_status():
    return _no_store(
        make_response(
            jsonify(
                identity=all_in_ai.status(),
                runtime=all_in_ai_runtime.status(),
            )
        )
    )


@bp.post("/all-in-ai/mission")
@web_security.login_required(api=True, founder_only=True)
def all_in_ai_mission():
    """Plan and durably receipt one Founder mission."""

    csrf_error = _require_csrf()
    if csrf_error is not None:
        return csrf_error
    identity = _founder_id()
    if identity is None:
        return _error("authentication_required", "Founder sign-in required.", 401)
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return _error("invalid_request", "A JSON object is required.", 400)

    try:
        result = all_in_ai_runtime.start_mission(
            identity,
            payload.get("mission"),
            task_type=payload.get("task_type", "GENERAL"),
            high_impact=bool(payload.get("high_impact", False)),
            research_mode=payload.get("research_mode", "standard"),
        )
    except ValueError as exc:
        return _error(str(exc), "Mission request failed validation.", 400)
    except all_in_ai_mission_store.MissionStoreUnavailable:
        return _error(
            "mission_receipt_unavailable",
            "The mission could not be durably receipted, so progression is blocked.",
            503,
        )

    return _no_store(make_response(jsonify(result), 201))


@bp.get("/all-in-ai/mission/<mission_id>")
@web_security.login_required(api=True, founder_only=True)
def all_in_ai_mission_read(mission_id: str):
    """Read back one owner-scoped mission with audit and HRM verification."""

    identity = _founder_id()
    if identity is None:
        return _error("authentication_required", "Founder sign-in required.", 401)
    try:
        receipt = all_in_ai_runtime.read_mission(identity, mission_id)
    except ValueError:
        return _error("invalid_mission_id", "Mission identifier is invalid.", 400)
    except all_in_ai_mission_store.MissionStoreUnavailable:
        return _error(
            "mission_receipt_unavailable",
            "The mission receipt could not be independently verified.",
            503,
        )
    return _no_store(make_response(jsonify(receipt=receipt)))


@bp.post("/all-in-ai/mission/<mission_id>/stop")
@web_security.login_required(api=True, founder_only=True)
def all_in_ai_mission_stop(mission_id: str):
    """Append a durable STOP checkpoint. STOP never grants execution."""

    csrf_error = _require_csrf()
    if csrf_error is not None:
        return csrf_error
    identity = _founder_id()
    if identity is None:
        return _error("authentication_required", "Founder sign-in required.", 401)
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return _error("invalid_request", "A JSON object is required.", 400)
    try:
        receipt = all_in_ai_runtime.stop_mission(
            identity,
            mission_id,
            expected_previous_hash=str(
                payload.get("expected_previous_hash") or ""
            ),
        )
    except ValueError:
        return _error("invalid_mission_id", "Mission identifier is invalid.", 400)
    except all_in_ai_mission_store.MissionStoreUnavailable:
        return _error(
            "mission_stop_unavailable",
            "STOP could not be durably verified, so progression remains blocked.",
            503,
        )
    except RuntimeError as exc:
        if str(exc) == "stale_mission_version":
            return _error(
                "stale_mission_version",
                "Mission state changed. Read the latest receipt before STOP.",
                409,
            )
        raise
    return _no_store(
        make_response(
            jsonify(
                receipt=receipt,
                stopped=True,
                execution_granted=False,
                human_authority_final=True,
            )
        )
    )


@bp.post("/all-in-ai/mission/<mission_id>/recover")
@web_security.login_required(api=True, founder_only=True)
def all_in_ai_mission_recover(mission_id: str):
    """Recover a STOPped mission to reviewable state only."""

    csrf_error = _require_csrf()
    if csrf_error is not None:
        return csrf_error
    identity = _founder_id()
    if identity is None:
        return _error("authentication_required", "Founder sign-in required.", 401)
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return _error("invalid_request", "A JSON object is required.", 400)
    try:
        receipt = all_in_ai_runtime.recover_mission(
            identity,
            mission_id,
            expected_previous_hash=str(
                payload.get("expected_previous_hash") or ""
            ),
        )
    except ValueError:
        return _error("invalid_mission_id", "Mission identifier is invalid.", 400)
    except all_in_ai_mission_store.MissionStoreUnavailable:
        return _error(
            "mission_recovery_unavailable",
            "Recovery could not be durably verified, so execution remains blocked.",
            503,
        )
    except RuntimeError as exc:
        if str(exc) == "mission_not_stopped":
            return _error(
                "mission_not_stopped",
                "Recovery is only available after a durable STOP checkpoint.",
                409,
            )
        if str(exc) == "stale_mission_version":
            return _error(
                "stale_mission_version",
                "Mission state changed. Read the latest receipt before recovery.",
                409,
            )
        raise
    return _no_store(
        make_response(
            jsonify(
                receipt=receipt,
                state="recovered_for_review",
                execution_granted=False,
                approval_granted=False,
                human_authority_final=True,
            )
        )
    )
