"""Founder-only ALL IN A.I. Command Center surface."""

from flask import Blueprint, jsonify, make_response, request

from . import all_in_ai, all_in_ai_runtime, web_security

bp = Blueprint("all_in_ai", __name__)


def _no_store(response):
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


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
    """Plan one Founder mission through the existing governed SMI intelligence spine."""

    if not web_security.csrf_valid(request):
        return _no_store(
            make_response(
                jsonify(
                    error={
                        "code": "csrf_failed",
                        "message": "The secure session expired. Refresh and try again.",
                    }
                ),
                403,
            )
        )

    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return _no_store(
            make_response(
                jsonify(
                    error={
                        "code": "invalid_request",
                        "message": "A JSON object is required.",
                    }
                ),
                400,
            )
        )

    try:
        plan = all_in_ai_runtime.plan_mission(
            payload.get("mission"),
            task_type=payload.get("task_type", "GENERAL"),
            high_impact=bool(payload.get("high_impact", False)),
            research_mode=payload.get("research_mode", "standard"),
        )
    except ValueError as exc:
        return _no_store(
            make_response(
                jsonify(
                    error={
                        "code": str(exc),
                        "message": "Mission request failed validation.",
                    }
                ),
                400,
            )
        )

    return _no_store(
        make_response(
            jsonify(
                plan=plan,
                execution_granted=False,
                approval_granted=False,
                human_authority_final=True,
            )
        )
    )
