"""Founder-only endpoints for SMI Green Gate and A7 certification evidence."""

from __future__ import annotations

import logging

from flask import Blueprint, jsonify, make_response, render_template, request

from . import (
    a7_certification,
    approval_service,
    authority,
    smi_proof_gate,
    web_security,
)

logger = logging.getLogger(__name__)

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


@bp.post("/runtime-guard")
@web_security.login_required(api=True, founder_only=True)
def runtime_guard_proof():
    """Run bounded recursion, duplicate-work and privilege-escalation guards."""

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
        proof = smi_proof_gate.run_runtime_guard_proof(str(user["id"]))
    except authority.HumanAuthorityRequired:
        return _error(
            "human_authority_required",
            "Only active level-zero Human Authority may record runtime guard proof.",
            403,
        )
    except ValueError as exc:
        return _error("invalid_proof_request", str(exc), 400)
    except RuntimeError:
        return _error(
            "runtime_guard_proof_unavailable",
            "Runtime guard proof could not be completed safely.",
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


@bp.post("/isolation-recovery")
@web_security.login_required(api=True, founder_only=True)
def isolation_recovery_proof():
    """Run bounded Aegis isolation plus full-state recovery proof."""

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
        proof = smi_proof_gate.run_isolation_recovery_proof(str(user["id"]))
    except authority.HumanAuthorityRequired:
        return _error(
            "human_authority_required",
            "Only active level-zero Human Authority may record isolation proof.",
            403,
        )
    except ValueError as exc:
        return _error("invalid_proof_request", str(exc), 400)
    except RuntimeError:
        return _error(
            "isolation_recovery_proof_unavailable",
            "Isolation recovery proof could not be completed safely.",
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


@bp.post("/founder-final")
@web_security.login_required(api=True, founder_only=True)
def founder_final_protocol():
    """Complete the 100% protocol only after a real Green Gate passes."""

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
        result = smi_proof_gate.complete_founder_final_protocol(str(user["id"]))
    except authority.HumanAuthorityRequired:
        return _error(
            "human_authority_required",
            "Only active level-zero Human Authority may complete Founder Final.",
            403,
        )
    except ValueError as exc:
        return _error("invalid_founder_final_request", str(exc), 400)
    except RuntimeError as exc:
        message = str(exc)
        if message.startswith("green_gate_incomplete:"):
            missing = tuple(filter(None, message.split(":", 1)[1].split(",")))
            logger.warning(
                "oap_smi_founder_final_blocked green_gate=false missing=%s",
                ",".join(missing),
            )
            return _no_store(
                make_response(
                    jsonify(
                        error={
                            "code": "green_gate_incomplete",
                            "message": "Founder Final remains locked until all Green Gate proof is present.",
                            "missing": missing,
                        },
                        green_gate=smi_proof_gate.public_safe_status(),
                        execution_granted=False,
                        human_authority_final=True,
                    ),
                    409,
                )
            )
        return _error(
            "founder_final_unavailable",
            "Founder Final could not be recorded safely.",
            503,
        )
    logger.info(
        "oap_smi_founder_final_recorded green_gate=true founder_final=true "
        "audit_recorded=%s execution_authority_expanded=false human_authority_final=true",
        bool(result.get("audit_recorded")),
    )
    return _no_store(
        make_response(
            jsonify(
                result=result,
                green_gate=smi_proof_gate.public_safe_status(),
                execution_granted=False,
                human_authority_final=True,
            )
        )
    )


@bp.post("/a6/readiness-bundle")
@web_security.login_required(api=True, founder_only=True)
def a6_readiness_bundle():
    """Record A6 readiness evidence without executing the approved operation."""

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
        proof = a7_certification.record_a6_readiness_bundle(
            identity_id=str(user["id"]),
            request_id=payload.get("request_id"),
            independent_evidence_ref=payload.get("independent_evidence_ref"),
            independent_evidence_hash=payload.get("independent_evidence_hash"),
            independent_issuer=payload.get("independent_issuer"),
        )
    except authority.HumanAuthorityRequired:
        return _error(
            "human_authority_required",
            "Only active level-zero Human Authority may record A6 readiness proof.",
            403,
        )
    except PermissionError as exc:
        return _error("a6_readiness_blocked", str(exc), 403)
    except ValueError as exc:
        return _error("invalid_a6_readiness_request", str(exc), 400)
    except RuntimeError as exc:
        return _error("a6_readiness_unavailable", str(exc), 503)
    return _no_store(
        make_response(
            jsonify(
                proof=proof,
                a6=a7_certification.public_safe_status(),
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
