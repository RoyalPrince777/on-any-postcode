"""Read-only Flask routes for the Mission Control vertical slice."""

from __future__ import annotations

from flask import Blueprint, jsonify, make_response, render_template, request

from . import status

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
