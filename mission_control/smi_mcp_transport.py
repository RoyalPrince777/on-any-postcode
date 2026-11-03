"""Opt-in, unmounted Flask JSON-RPC MCP transport for read-only OAP SMI tools.

This blueprint is NOT registered by default. A production integrator must provide
trusted OAuth policy, current revocation/introspection decision, HTTPS termination,
rate limits, CORS/origin policy, and audited first-party deployment before mounting.
No access from browser sessions or request-supplied settings.
"""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from flask import Blueprint, jsonify, request

from .smi_authenticated_dispatch import verified_readonly_dispatch
from .smi_connector_dispatch import SUPPORTED
from .smi_mcp_token_gate import TokenRejected, TrustedTokenPolicy, verify_readonly_token

PROTOCOL_VERSION = "2025-06-18"
MAX_REQUEST_BYTES = 16_384


def create_smi_mcp_blueprint(
    *,
    policy: TrustedTokenPolicy,
    token_active: Callable[[str], bool],
    allowed_browser_origin: str | None = None,
) -> Blueprint:
    """Construct ONLY; never implicitly register an accessible route."""
    if not isinstance(policy, TrustedTokenPolicy) or not callable(token_active):
        raise TypeError("trusted_mcp_authentication_required")
    if allowed_browser_origin is not None and (
        not isinstance(allowed_browser_origin, str)
        or not allowed_browser_origin.startswith("https://")
        or "/" in allowed_browser_origin.removeprefix("https://")
    ):
        raise ValueError("trusted_browser_origin_required")
    bp = Blueprint("oap_smi_mcp", __name__)

    @bp.route("/mission/smi/mcp", methods=["POST"])
    def mcp():
        # MCP browser origin is a separate trust boundary from bearer authentication.
        # No configured origin means reject all browser-originated requests.
        browser_origin = request.headers.get("Origin")
        if browser_origin is not None and browser_origin != allowed_browser_origin:
            response = jsonify(error="forbidden_origin")
            response.headers["Cache-Control"] = "no-store"
            return response, 403
        if request.content_length is None or request.content_length > MAX_REQUEST_BYTES:
            return jsonify(error="invalid_request"), 400
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer ") or auth.count(" ") != 1:
            return jsonify(error="unauthorized"), 401
        token = auth[7:]
        try:
            verify_readonly_token(token, policy=policy)
            # A live server-side revocation decision is mandatory, not a JWT claim.
            if token_active(token) is not True:
                raise TokenRejected("invalid_access_token")
        except Exception:  # noqa: BLE001 - do not disclose auth failures or allow revocation outages.
            return jsonify(error="unauthorized"), 401

        payload = request.get_json(silent=True)
        if not isinstance(payload, dict) or payload.get("jsonrpc") != "2.0":
            return jsonify(jsonrpc="2.0", id=None, error={"code": -32600, "message": "Invalid Request"}), 400
        request_id: Any = payload.get("id")
        if type(request_id) not in (int, str):
            return jsonify(jsonrpc="2.0", id=None, error={"code": -32600, "message": "Invalid Request"}), 400
        method = payload.get("method")
        params = payload.get("params", {})
        if not isinstance(params, dict):
            return jsonify(jsonrpc="2.0", id=request_id, error={"code": -32602, "message": "Invalid params"}), 400
        if method == "initialize":
            result = {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": {"name": "oap-smi-readonly", "version": "0.1.0"},
            }
        elif method == "tools/list":
            result = {"tools": [
                {
                    "name": name,
                    "description": "Read-only OAP SMI status" if name == "smi_status" else "Read-only OAP Studio capabilities",
                    "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
                    "annotations": {"readOnlyHint": True},
                }
                for name in SUPPORTED
            ]}
        elif method == "tools/call":
            name = params.get("name")
            arguments = params.get("arguments", {})
            try:
                response = verified_readonly_dispatch(
                    bearer_token=token, policy=policy, tool_name=name, arguments=arguments,
                )
            except (PermissionError, ValueError):
                return jsonify(jsonrpc="2.0", id=request_id, error={"code": -32602, "message": "Tool unavailable"}), 400
            result = {"content": [{"type": "text", "text": __import__("json").dumps(response)}], "isError": False}
        else:
            return jsonify(jsonrpc="2.0", id=request_id, error={"code": -32601, "message": "Method not found"}), 404
        output = jsonify(jsonrpc="2.0", id=request_id, result=result)
        output.headers["Cache-Control"] = "no-store"
        return output

    return bp
