"""Founder-only HTTP entry for the governed Signal action pipeline."""
from __future__ import annotations

from flask import Blueprint, jsonify, make_response, request

from . import governed_signal_pipeline, web_security

bp = Blueprint("governed_signal_pipeline", __name__)


def _no_store(response):
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


def _error(code: str, message: str, status_code: int):
    return _no_store(
        make_response(jsonify(error={"code": code, "message": message}), status_code)
    )


@bp.post("/mission/smi/governed-signal")
@web_security.login_required(api=True, founder_only=True)
def governed_signal():
    """Run the canonical review chain; external execution remains adapter-gated."""

    if not web_security.csrf_valid(request):
        return _error("csrf_invalid", "Session expired. Refresh and try again.", 403)
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return _error("invalid_request", "A JSON object is required.", 400)
    content = str(payload.get("content") or "").strip()
    if not content:
        return _error("content_required", "Signal content is required.", 400)

    identity_id = web_security.authenticated_identity()
    try:
        result = governed_signal_pipeline.run(
            request_id=str(payload.get("request_id") or request.headers.get("X-Request-ID") or "").strip(),
            identity_id=identity_id,
            content=content,
            sender=str(payload.get("sender") or "Neo"),
            requested_action=str(payload.get("requested_action") or "review"),
            consequential=payload.get("consequential") is True,
            private_data=payload.get("private_data") is True,
            human_authority_approved=payload.get("human_authority_approved") is True,
            authority_context={
                "authority_level": 0,
                "permissions": ("REQUEST_RECOMMENDATION", "APPROVE_RECOMMENDATION"),
                "is_human_authority": True,
            },
            action_executor=None,
            receipt_writer=None,
        )
    except ValueError as exc:
        return _error("invalid_request", str(exc), 400)

    return _no_store(make_response(jsonify(result)))
