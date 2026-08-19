"""
Mission Control read-only views.
Three modes: sovereign, mission, approval.
GET only; no mutations.
"""
from flask import request, jsonify, render_template
from . import status as mc_status


VALID_MODES = {"sovereign", "mission", "approval"}


def mission_index():
    """
    GET /mission and GET /mission/
    Show mode selector or mode-specific view.
    Validates mode parameter.
    """
    mode = request.args.get("mode", "").lower().strip()
    
    if mode and mode not in VALID_MODES:
        return jsonify({
            "error": "Invalid mode",
            "valid_modes": list(VALID_MODES),
            "message": f"Mode '{mode}' not recognized. Use one of: {', '.join(sorted(VALID_MODES))}"
        }), 400
    
    # If no mode specified, show selector
    if not mode:
        return render_template(
            "mission_control/mission.html",
            mode=None,
            status=mc_status.get_public_gateway_status(),
        )
    
    # Render mode-specific dashboard
    return render_template(
        "mission_control/mission.html",
        mode=mode,
        status=mc_status.get_public_gateway_status(),
        agents=mc_status.get_agent_statuses(),
        approval_counts=mc_status.get_approval_summary(),
        timeline=mc_status.get_latest_timeline(limit=5),
    )


def mission_status():
    """
    GET /mission/status
    Return public gateway status as JSON.
    No privileged scope checks yet (blocked until auth is real).
    """
    # Check for invalid privileged scope requests
    scope = request.args.get("scope", "public").lower().strip()
    if scope != "public":
        return jsonify({
            "error": "Forbidden",
            "message": "Privileged scope requires real Identity and Permission checks. Not yet implemented."
        }), 403
    
    status_data = mc_status.get_public_gateway_status()
    return jsonify(status_data), 200
