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
