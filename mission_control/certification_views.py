"""Founder-only certification control routes.

These routes expose OAP identity certifications without creating accounts,
granting permissions or widening Founder access.
"""
from __future__ import annotations

import json
import os
import threading

from flask import Blueprint, jsonify, make_response, request

from . import certification, hrm_readonly_probe, postgres_db, web_security

bp = Blueprint("certification", __name__)


def _database_startup_probe() -> None:
    """Emit only coarse PostgreSQL readiness after a hosted process starts."""

    snapshot = postgres_db.postgres_status()
    proof = {
        "event": "oap_database_startup_probe",
        "backend": snapshot.get("backend"),
        "source": snapshot.get("source"),
        "configured": bool(snapshot.get("configured")),
        "reachable": bool(snapshot.get("reachable")),
        "initialized": bool(snapshot.get("initialized")),
        "pending_migrations": len(snapshot.get("pending") or ()),
        "checksum_mismatch": bool(snapshot.get("checksum_mismatches")),
        "error": snapshot.get("error"),
        "read_only": True,
        "secret_exposed": False,
    }
    print(json.dumps(proof, separators=(",", ":"), sort_keys=True), flush=True)


def _hrm_candidate_startup_probe() -> None:
    """Emit only presence/reachability for an existing HRM Postgres alias."""

    snapshot = hrm_readonly_probe.status()
    proof = {
        "event": "oap_hrm_candidate_startup_probe",
        "backend": snapshot.get("backend"),
        "source": snapshot.get("source"),
        "configured": bool(snapshot.get("configured")),
        "reachable": bool(snapshot.get("reachable")),
        "error": snapshot.get("error"),
        "read_only": True,
        "write_performed": False,
        "schema_changed": False,
        "secret_exposed": False,
    }
    print(json.dumps(proof, separators=(",", ":"), sort_keys=True), flush=True)


def _startup_probes() -> None:
    _database_startup_probe()
    _hrm_candidate_startup_probe()


@bp.record_once
def _schedule_database_startup_probe(_state) -> None:
    """Keep local/tests quiet; Render gets non-blocking read-only proofs."""

    if os.environ.get("RENDER", "").strip().casefold() != "true":
        return
    threading.Thread(
        target=_startup_probes,
        name="oap-database-startup-probes",
        daemon=True,
    ).start()


def _no_store(response):
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


def _error(code: str, message: str, status_code: int):
    return _no_store(
        make_response(jsonify(error={"code": code, "message": message}), status_code)
    )


def _payload() -> dict[str, object]:
    value = request.get_json(silent=True)
    if not isinstance(value, dict):
        raise TypeError("json_object_required")
    return value


@bp.get("/certifications/status")
@bp.get("/smi/certifications")
@web_security.login_required(api=True, founder_only=True)
def certification_status():
    """Return redacted certification readiness and counts."""

    return _no_store(make_response(jsonify(certification.status())))


@bp.get("/certifications/identity/<identity_id>")
@web_security.login_required(api=True, founder_only=True)
def certification_identity_status(identity_id: str):
    """Return certification state for one existing OAP identity."""

    try:
        return _no_store(make_response(jsonify(certification.identity_status(identity_id))))
    except ValueError as exc:
        return _error("invalid_request", str(exc), 400)
    except certification.CertificationUnavailable:
        return _error(
            "certification_unavailable",
            "Certification state is temporarily unavailable.",
            503,
        )


@bp.post("/certifications/grant")
@web_security.login_required(api=True, founder_only=True)
def certification_grant():
    """Grant Creator or Merchant certification after explicit Founder approval."""

    if not web_security.csrf_valid(request):
        return _error("csrf_invalid", "Session expired. Refresh and try again.", 403)
    try:
        payload = _payload()
        result = certification.grant(
            target_identity_id=payload.get("identity_id"),
            certification_kind=payload.get("kind"),
            granted_by_identity_id=web_security.authenticated_identity(),
            human_authority_approved=payload.get("human_authority_approved") is True,
        )
        return _no_store(make_response(jsonify(result), 201))
    except TypeError as exc:
        return _error("invalid_request", str(exc), 400)
    except ValueError as exc:
        return _error("invalid_request", str(exc), 400)
    except PermissionError as exc:
        return _error("human_authority_required", str(exc), 403)
    except certification.CertificationUnavailable:
        return _error(
            "certification_unavailable",
            "Certification could not be recorded safely.",
            503,
        )


@bp.post("/certifications/revoke")
@web_security.login_required(api=True, founder_only=True)
def certification_revoke():
    """Revoke Creator or Merchant certification after explicit Founder approval."""

    if not web_security.csrf_valid(request):
        return _error("csrf_invalid", "Session expired. Refresh and try again.", 403)
    try:
        payload = _payload()
        result = certification.revoke(
            target_identity_id=payload.get("identity_id"),
            certification_kind=payload.get("kind"),
            revoked_by_identity_id=web_security.authenticated_identity(),
            human_authority_approved=payload.get("human_authority_approved") is True,
        )
        return _no_store(make_response(jsonify(result)))
    except TypeError as exc:
        return _error("invalid_request", str(exc), 400)
    except ValueError as exc:
        return _error("invalid_request", str(exc), 400)
    except PermissionError as exc:
        return _error("human_authority_required", str(exc), 403)
    except certification.CertificationUnavailable:
        return _error(
            "certification_unavailable",
            "Certification could not be revoked safely.",
            503,
        )
