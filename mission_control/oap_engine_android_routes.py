"""Public, bounded OAP Engine document endpoint for Android."""
from __future__ import annotations

import os
from urllib.parse import urlsplit

from flask import Blueprint, current_app, jsonify, request

from oap.browser_engine.android_route import render_supported_target

bp = Blueprint("oap_engine_android", __name__)

DEFAULT_OAP_PUBLIC_ORIGIN = "https://on-any-postcode.onrender.com"


def _public_origin() -> str:
    candidate = os.environ.get("OAP_PUBLIC_ORIGIN", DEFAULT_OAP_PUBLIC_ORIGIN).strip()
    parsed = urlsplit(candidate)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        return DEFAULT_OAP_PUBLIC_ORIGIN
    if parsed.path not in {"", "/"} or parsed.query or parsed.fragment:
        return DEFAULT_OAP_PUBLIC_ORIGIN
    return candidate.rstrip("/") + "/"

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
            base_url=_public_origin(),
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
