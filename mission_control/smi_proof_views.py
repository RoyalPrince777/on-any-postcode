"""Founder-only endpoints for SMI Green Gate evidence and rollback proof."""

from __future__ import annotations

from flask import Blueprint, jsonify, make_response, request

from . import authority, smi_proof_gate, web_security

bp = Blueprint("smi_proof_gate", __name__, url_prefix="/mission/smi-proof")


def _no_store(response):
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


def _error(code: str, message: str, status_code: int):
    return _no_store(
        make_response(jsonify(error={"code": code, "message": message}), status_code)
    )


@bp.get("/status")
@web_security.login_required(api=True)
def proof_status():
    """Return coarse Green Gate truth without receipt or identity material."""

    return _no_store(make_response(jsonify(smi_proof_gate.public_safe_status())))


@bp.post("/rollback-recovery")
@web_security.login_required(api=True)
def rollback_recovery_proof():
    """Run one bounded restore proof; never mutate product state or grant execution."""

    if not web_security.csrf_valid(request):
        return _error(
            "csrf_failed",
            "The secure session expired. Refresh the page and try again.",
            403,
        )
    user = web_security.current_authenticated_user()
    if user is None:
        return _error("authentication_required", "Founder sign-in required.", 401)
    try:
        proof = smi_proof_gate.run_rollback_recovery_proof(str(user["id"]))
    except authority.HumanAuthorityRequired:
        return _error(
            "human_authority_required",
            "Only active level-zero Human Authority may record rollback proof.",
            403,
        )
    except ValueError as exc:
        return _error("invalid_proof_request", str(exc), 400)
    except RuntimeError:
        return _error(
            "rollback_proof_unavailable",
            "Rollback proof could not be completed safely.",
            503,
        )
    return _no_store(
        make_response(
            jsonify(
                proof=proof,
                green_gate=smi_proof_gate.public_safe_status(),
                execution_granted=False,
                human_authority_final=True,
            )
        )
    )
