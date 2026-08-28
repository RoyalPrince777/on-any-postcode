"""Authenticated applicant and Human Authority Movement certification surfaces."""
from __future__ import annotations

from flask import Blueprint, jsonify, make_response, render_template, request

from . import authority, movement_certification, web_security

bp = Blueprint("movement_certification", __name__)


def _no_store(response):
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


def _error(code: str, message: str, status_code: int):
    return _no_store(
        make_response(jsonify(error={"code": code, "message": message}), status_code)
    )


def _body() -> dict:
    value = request.get_json(silent=True)
    if not isinstance(value, dict):
        raise TypeError("json_object_required")
    return value


def _guard(identity_id: str):
    if not web_security.csrf_valid(request):
        return _error("csrf_failed", "Request verification failed.", 403)
    if not web_security.PUBLIC_WRITE_LIMITER.allow(identity_id):
        return _error("rate_limited", "Too many Movement requests.", 429)
    return None


def _operation_error(exc: Exception):
    if isinstance(exc, authority.HumanAuthorityRequired):
        return _error(
            "level_zero_human_authority_required",
            "Human Authority approval is required.",
            403,
        )
    if isinstance(exc, movement_certification.CertificationUnavailable):
        return _error(
            "movement_certification_unavailable",
            "Movement certification is temporarily unavailable.",
            503,
        )
    if isinstance(exc, (TypeError, ValueError)):
        return _error(
            str(exc) or "invalid_certification_request",
            "Invalid certification request.",
            400,
        )
    return _error(
        "movement_certification_unavailable",
        "Movement certification is temporarily unavailable.",
        503,
    )


@bp.get("/movement/certification")
@web_security.login_required()
def applicant_home():
    """Show only the authenticated person's applications and safe declaration form."""

    user = web_security.current_authenticated_user()
    if user is None:  # pragma: no cover - decorator fails closed first.
        return _error("authentication_required", "Sign in required.", 401)
    try:
        applications = movement_certification.own_applications(user["id"])
        response = make_response(
            render_template(
                "movement_certification.html",
                applications=applications,
                certification_status=movement_certification.schema_status(),
                application_notice={
                    "version": movement_certification.APPLICATION_NOTICE_VERSION,
                    "digest": movement_certification.APPLICATION_NOTICE_DIGEST,
                    "text": movement_certification.APPLICATION_NOTICE_TEXT,
                    "retention_days": movement_certification.RETENTION_DAYS,
                },
            )
        )
        return _no_store(response)
    except Exception as exc:  # noqa: BLE001 - page boundary redacts backend detail.
        return _operation_error(exc)


@bp.post("/movement/worker-applications")
@web_security.login_required(api=True)
def submit_application():
    """Submit one internal application; never grant a Movement worker role."""

    user = web_security.current_authenticated_user()
    if user is None:  # pragma: no cover
        return _error("authentication_required", "Sign in required.", 401)
    identity = str(user["id"])
    if guard := _guard(identity):
        return guard
    try:
        body = _body()
        result = movement_certification.submit_application(
            user=user,
            role_type=body.get("role_type"),
            vehicle_type=body.get("vehicle_type"),
            service_zone=body.get("service_zone", ""),
            declarations=body.get("declarations"),
            vehicle_label=body.get("vehicle_label", ""),
            registration_last4=body.get("registration_last4", ""),
        )
        return _no_store(make_response(jsonify(application=result), 201))
    except Exception as exc:  # noqa: BLE001 - API boundary redacts backend detail.
        return _operation_error(exc)


@bp.post("/movement/worker-applications/<application_id>/resubmit")
@web_security.login_required(api=True)
def resubmit_application(application_id: str):
    """Let the owning applicant answer NEEDS_INFO without an external channel."""

    identity = web_security.authenticated_identity()
    if guard := _guard(identity):
        return guard
    try:
        body = _body()
        result = movement_certification.resubmit_application(
            identity_id=identity,
            application_id=application_id,
            service_zone=body.get("service_zone", ""),
            declarations=body.get("declarations"),
            response_message=body.get("response_message"),
            vehicle_label=body.get("vehicle_label", ""),
            registration_last4=body.get("registration_last4", ""),
        )
        return _no_store(make_response(jsonify(application=result), 200))
    except Exception as exc:  # noqa: BLE001 - API boundary redacts backend detail.
        return _operation_error(exc)


@bp.post("/movement/worker-applications/<application_id>/cancel")
@web_security.login_required(api=True)
def cancel_application(application_id: str):
    """Withdraw an owned application and scrub optional personal fields."""

    identity = web_security.authenticated_identity()
    if guard := _guard(identity):
        return guard
    try:
        result = movement_certification.cancel_application(
            identity_id=identity,
            application_id=application_id,
        )
        return _no_store(make_response(jsonify(application=result), 200))
    except Exception as exc:  # noqa: BLE001 - API boundary redacts backend detail.
        return _operation_error(exc)


@bp.delete("/movement/worker-applications/<application_id>")
@web_security.login_required(api=True)
def delete_application(application_id: str):
    """Delete a closed, applicant-owned application and cascading private data."""

    identity = web_security.authenticated_identity()
    if guard := _guard(identity):
        return guard
    try:
        result = movement_certification.delete_application(
            identity_id=identity,
            application_id=application_id,
        )
        return _no_store(make_response(jsonify(application=result), 200))
    except Exception as exc:  # noqa: BLE001 - API boundary redacts backend detail.
        return _operation_error(exc)


@bp.get("/mission/movement-certification")
@web_security.login_required()
def authority_home():
    """Private Human Authority queue; public Mission boundary still hides this path."""

    identity = web_security.authenticated_identity()
    try:
        queue = movement_certification.review_queue(identity)
        response = make_response(
            render_template(
                "movement_certification_review.html",
                queue=queue,
                certification_status=movement_certification.schema_status(),
            )
        )
        return _no_store(response)
    except Exception as exc:  # noqa: BLE001 - private boundary redacts backend detail.
        return _operation_error(exc)


@bp.post("/mission/movement-certification/<application_id>/review")
@web_security.login_required(api=True)
def review_application(application_id: str):
    """Record Human Authority review only; role grant remains fail-closed."""

    identity = web_security.authenticated_identity()
    if guard := _guard(identity):
        return guard
    try:
        body = _body()
        result = movement_certification.review_application(
            reviewer_identity_id=identity,
            application_id=application_id,
            decision=body.get("decision"),
            reason=body.get("reason"),
            applicant_message=body.get("applicant_message", ""),
        )
        return _no_store(make_response(jsonify(review=result), 200))
    except Exception as exc:  # noqa: BLE001 - API boundary redacts backend detail.
        return _operation_error(exc)


@bp.post("/mission/movement-certification/purge-expired")
@web_security.login_required(api=True)
def purge_expired_applications():
    """Delete expired records only after an explicit Human Authority request."""

    identity = web_security.authenticated_identity()
    if guard := _guard(identity):
        return guard
    try:
        body = _body()
        if body.get("confirm") != "PURGE_EXPIRED":
            raise ValueError("purge_confirmation_required")
        result = movement_certification.purge_expired_applications(
            reviewer_identity_id=identity,
        )
        return _no_store(make_response(jsonify(purge=result), 200))
    except Exception as exc:  # noqa: BLE001 - API boundary redacts backend detail.
        return _operation_error(exc)
