"""Public, bounded OAP Engine document endpoint for Android."""
from __future__ import annotations

from flask import Blueprint, current_app, jsonify, request

from oap.browser_engine.android_route import render_supported_target

bp = Blueprint("oap_engine_android", __name__)

@bp.get("/api/oap-engine/document")
def oap_engine_document():
    target = request.args.get("path", "")
    try:
        viewport_width = int(request.args.get("viewport", "390"))
    except ValueError:
        return jsonify({"error": "invalid_viewport"}), 400

    try:
        document = render_supported_target(
            current_app,
            target,
            viewport_width=viewport_width,
        )
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    if document is None:
        return jsonify(
            {
                "error": "unsupported_oap_engine_target",
                "fallback": "WEBVIEW",
                "human_authority_final": True,
            }
        ), 404

    response = jsonify(document)
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-OAP-Renderer"] = "OAP_ENGINE"
    return response
