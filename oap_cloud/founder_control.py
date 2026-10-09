"""Founder-private OAP Cloud control-plane foundation.

No infrastructure provisioning, storage backend or remote job execution is implied.
"""
import os
from flask import Blueprint, jsonify, request

cloud_bp = Blueprint("oap_cloud_v1", __name__)

def _founder_authorized():
    # Fail closed: deployment must provide an independently secured gateway.
    # Never accept founder identity from request headers, query or cookies here.
    token = os.environ.get("OAP_CLOUD_FOUNDER_TOKEN", "")
    supplied = request.headers.get("Authorization", "")
    if not token or not supplied.startswith("Bearer "):
        return False
    import hmac
    return hmac.compare_digest(supplied[7:], token)

@cloud_bp.before_request
def founder_gate():
    if not _founder_authorized():
        return jsonify({"error": "not_found"}), 404

@cloud_bp.get("/cloud/v1/status")
def cloud_status():
    return jsonify({
        "system": "OAP Cloud",
        "access": "founder_private",
        "control_plane": "foundation",
        "storage": "not_provisioned",
        "compute": "not_provisioned",
        "os_image": "not_built",
        "os_boot": "not_proven",
        "security_recovery": "not_tested",
    })
