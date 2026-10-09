"""Founder-private OAP Cloud control-plane foundation.

No infrastructure provisioning, storage backend or remote job execution is implied.
"""
import base64
import binascii
import hmac
import os
from pathlib import Path

from flask import Blueprint, jsonify, request

from mission_control import neon_auth, web_security

from .drive_storage import DriveStorage

cloud_bp = Blueprint("oap_cloud_v1", __name__)

def _founder_authorized():
    # Fail closed: deployment must provide an independently secured gateway.
    # Never accept founder identity from request headers, query or cookies here.
    token = os.environ.get("OAP_CLOUD_FOUNDER_TOKEN", "")
    supplied = request.headers.get("Authorization", "")
    if not token or not supplied.startswith("Bearer "):
        return False
    return hmac.compare_digest(supplied[7:], token)

@cloud_bp.before_request
def founder_gate():
    if not _founder_authorized():
        return jsonify({"error": "not_found"}), 404
    # A bootstrap bearer token alone never grants Founder authority.
    # Require OAP's canonical managed identity and Founder policy too.
    try:
        user = web_security.current_authenticated_user()
        if not user or user.get("recovery_founder") or not web_security.private_authority_allowed(user):
            return jsonify({"error": "not_found"}), 404
    except neon_auth.AuthUnavailable:
        return jsonify({"error": "not_found"}), 404
    # Mutating operations require the managed session CSRF secret in addition
    # to both the bootstrap bearer token and Founder authority.
    if request.method == "POST" and not web_security.csrf_valid(request):
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

@cloud_bp.post("/cloud/v1/drive/artifacts")
def drive_upload():
    """Founder-only upload; unavailable until an operator configures private storage."""
    root = os.environ.get("OAP_DRIVE_STORAGE_ROOT")
    if not root:
        return jsonify({"error": "storage_not_provisioned"}), 503
    if not request.is_json:
        return jsonify({"error": "invalid_manifest"}), 400
    manifest = request.get_json(silent=True)
    if not isinstance(manifest, dict):
        return jsonify({"error": "invalid_manifest"}), 400
    # Payload arrives as strict base64 inside JSON; no filename or path is accepted.
    manifest = dict(manifest)
    encoded = manifest.pop("payload_base64", None)
    if not isinstance(encoded, str) or len(encoded) > 20_000_000:
        return jsonify({"error": "invalid_payload"}), 400
    try:
        payload = base64.b64decode(encoded, validate=True)
        store = DriveStorage(Path(root))
        digest = store.put(manifest, payload)
    except (ValueError, OSError, binascii.Error):
        return jsonify({"error": "artifact_rejected"}), 400
    return jsonify({"sha256": digest, "stored": True}), 201

@cloud_bp.post("/cloud/v1/drive/retrieve")
def drive_retrieve():
    """Founder-only verified retrieval, disabled without configured storage."""
    root = os.environ.get("OAP_DRIVE_STORAGE_ROOT")
    if not root:
        return jsonify({"error": "storage_not_provisioned"}), 503
    manifest = request.get_json(silent=True) if request.is_json else None
    if not isinstance(manifest, dict):
        return jsonify({"error": "invalid_manifest"}), 400
    try:
        payload = DriveStorage(Path(root)).get(manifest)
    except (ValueError, FileNotFoundError, OSError):
        return jsonify({"error": "artifact_unavailable"}), 404
    return jsonify({"payload_base64": base64.b64encode(payload).decode("ascii"),
                    "sha256": manifest["sha256"]}), 200
