"""Private-gateway-only route for safe SMI runtime certification."""
from __future__ import annotations

import os

from flask import Blueprint, jsonify, make_response

from . import smi_certification

bp = Blueprint("smi_certification", __name__)


@bp.get("/api/smi/thinking-certification")
def thinking_certification():
    """Expose only coarse read-only certification through the signed SMI gateway."""

    # Imported lazily to avoid a module-registration cycle with surface_security.
    from . import surface_security

    if not surface_security.gateway_authorized():
        response = make_response("", 404)
        response.headers["Cache-Control"] = "no-store"
        return response

    snapshot = smi_certification.certify()
    certified = bool(snapshot.get("certified"))
    revision = (
        os.environ.get("RENDER_GIT_COMMIT", "").strip()
        or os.environ.get("OAP_ENV_REVISION", "").strip()
        or "unknown"
    )
    response = jsonify(
        status="certified" if certified else "unavailable",
        signal="🟢" if certified else "🔴",
        certification={
            "name": snapshot["name"],
            "version": snapshot["version"],
            "probe_kind": snapshot["probe_kind"],
            "passed": snapshot["passed"],
            "total": snapshot["total"],
            "stage_count": snapshot["stage_count"],
            "stages": snapshot["stages"],
            "checks": snapshot["checks"],
            "provider_called": snapshot["provider_called"],
            "hrm_written": snapshot["hrm_written"],
            "founder_session_created": snapshot["founder_session_created"],
            "private_reasoning_exposed": snapshot["private_reasoning_exposed"],
            "decision_authority": snapshot["decision_authority"],
            "execution_authority": snapshot["execution_authority"],
            "human_authority_final": snapshot["human_authority_final"],
        },
        gateway_authorized=True,
        founder_auth_bypassed=False,
        revision=revision[:12],
    )
    response.status_code = 200 if certified else 503
    response.headers["Cache-Control"] = "no-store"
    return response



@bp.post("/api/smi/investigation-case")
def investigation_case():
    """Prepare an unverified evidence case behind the existing signed gateway."""
    from flask import request

    from oap.smi.research_intelligence import build_investigation_case

    from . import surface_security

    if not surface_security.gateway_authorized():
        response = make_response("", 404)
        response.headers["Cache-Control"] = "no-store"
        return response
    if request.content_length is None or request.content_length > 32768:
        response = jsonify(error="invalid_case_size")
        response.status_code = 413
    else:
        body = request.get_json(silent=True)
        if not isinstance(body, dict):
            response = jsonify(error="invalid_case")
            response.status_code = 400
        elif not isinstance(body.get("evidence"), list) or len(body["evidence"]) > 40:
            response = jsonify(error="invalid_evidence")
            response.status_code = 400
        else:
            try:
                case = build_investigation_case(
                    body.get("case_id", ""),
                    body.get("question", ""),
                    body["evidence"],
                )
            except (TypeError, ValueError):
                response = jsonify(error="invalid_case")
                response.status_code = 400
            else:
                response = jsonify(case)
                response.status_code = 200
    response.headers["Cache-Control"] = "no-store"
    return response
