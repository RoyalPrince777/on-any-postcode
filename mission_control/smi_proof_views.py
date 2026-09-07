"""Founder-only endpoints for SMI Green Gate and A7 certification evidence."""

from __future__ import annotations

from flask import Blueprint, jsonify, make_response, render_template, request

from . import (
    a7_certification,
    approval_service,
    authority,
    smi_proof_gate,
    web_security,
)

bp = Blueprint(
    "smi_proof_gate",
    __name__,
    url_prefix="/mission/smi-proof",
    template_folder="templates",
)


def _no_store(response):
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


def _error(code: str, message: str, status_code: int):
    return _no_store(
        make_response(jsonify(error={"code": code, "message": message}), status_code)
    )


@bp.get("/status")
@web_security.login_required(api=True, founder_only=True)
def proof_status():
    """Return coarse Green Gate truth without receipt or identity material."""

    return _no_store(make_response(jsonify(smi_proof_gate.public_safe_status())))


@bp.post("/rollback-recovery")
@web_security.login_required(api=True, founder_only=True)
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


@bp.get("/a7")
@web_security.login_required(founder_only=True)
def a7_dashboard():
    """Render the Founder-only A7 proof and certification readiness screen."""

    return _no_store(
        make_response(
            render_template(
                "smi_a7.html",
                a7=a7_certification.public_safe_status(),
                green_gate=smi_proof_gate.public_safe_status(),
                approval=approval_service.status(),
                oap_csrf_token=web_security.csrf_token(),
            )
        )
    )


@bp.get("/a7/status")
@web_security.login_required(api=True, founder_only=True)
def a7_status():
    """Return fail-closed A7 readiness without granting certification."""

    return _no_store(make_response(jsonify(a7_certification.public_safe_status())))


@bp.post("/a7/emergency-halt")
@web_security.login_required(api=True, founder_only=True)
def a7_emergency_halt_proof():
    """Run the bounded A7 halt proof with Human-only resume semantics."""

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
        proof = a7_certification.run_emergency_halt_proof(str(user["id"]))
    except authority.HumanAuthorityRequired:
        return _error(
            "human_authority_required",
            "Only active level-zero Human Authority may record A7 halt proof.",
            403,
        )
    except ValueError as exc:
        return _error("invalid_proof_request", str(exc), 400)
    except RuntimeError:
        return _error(
            "emergency_halt_proof_unavailable",
            "Emergency-halt proof could not be completed safely.",
            503,
        )
    return _no_store(
        make_response(
            jsonify(
                proof=proof,
                a7=a7_certification.public_safe_status(),
                execution_granted=False,
                human_authority_final=True,
            )
        )
    )


@bp.post("/a7/evidence")
@web_security.login_required(api=True, founder_only=True)
def a7_evidence_reference():
    """Record a reviewed A6/A7 evidence hash; never self-certify external truth."""

    if not web_security.csrf_valid(request):
        return _error(
            "csrf_failed",
            "The secure session expired. Refresh the page and try again.",
            403,
        )
    user = web_security.current_authenticated_user()
    if user is None:
        return _error("authentication_required", "Founder sign-in required.", 401)
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return _error("invalid_request", "A JSON object is required.", 400)
    try:
        receipt = a7_certification.record_evidence_reference(
            identity_id=str(user["id"]),
            assurance=payload.get("assurance"),
            evidence_ref=payload.get("evidence_ref"),
            evidence_hash=payload.get("evidence_hash"),
            issuer=payload.get("issuer"),
            scope=payload.get("scope"),
            attestor_type=payload.get("attestor_type"),
        )
    except authority.HumanAuthorityRequired:
        return _error(
            "human_authority_required",
            "Only active level-zero Human Authority may record A7 evidence.",
            403,
        )
    except ValueError as exc:
        return _error("invalid_evidence_reference", str(exc), 400)
    except Exception:  # noqa: BLE001 - evidence intake must fail closed.
        return _error(
            "a7_evidence_store_unavailable",
            "A7 evidence could not be recorded safely.",
            503,
        )
    return _no_store(
        make_response(
            jsonify(
                receipt=receipt,
                a7=a7_certification.public_safe_status(),
                certification_granted=False,
                execution_granted=False,
                human_authority_final=True,
            )
        )
    )
