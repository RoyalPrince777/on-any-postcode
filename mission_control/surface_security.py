"""Network-facing boundary between public OAP and private SMI surfaces."""
from __future__ import annotations

import hmac
import os

from flask import Flask, make_response, request

_GATEWAY_HEADER = "X-OAP-SMI-Gateway"
_PRIVATE_PATH_PREFIXES = (
    "/mission",
    "/auth",
    "/enter-my-world",
    "/my-world",
    "/myworld",
    "/infrastructure",
    "/api/infrastructure",
)
_LINK_DEVICE_PATHS = frozenset({"/linkup"})
_LINK_PERMISSIONS_POLICY = (
    "camera=(self), microphone=(self), geolocation=(self), payment=()"
)


def gateway_configured() -> bool:
    return bool(os.environ.get("OAP_SMI_GATEWAY_SECRET", "").strip())


def gateway_authorized() -> bool:
    expected = os.environ.get("OAP_SMI_GATEWAY_SECRET", "").strip()
    supplied = request.headers.get(_GATEWAY_HEADER, "")
    return bool(expected and supplied) and hmac.compare_digest(expected, supplied)


def _is_private_path(path: str) -> bool:
    clean = path.rstrip("/") or "/"
    return any(
        clean == prefix or clean.startswith(prefix + "/")
        for prefix in _PRIVATE_PATH_PREFIXES
    )


def register(app: Flask) -> None:
    """Hide Founder surfaces and keep device capability permissions route-scoped.

    Once the SMI gateway secret is configured, protected paths can only be
    reached through the private gateway that supplies the shared header. Direct
    requests to the public origin receive a non-advertising 404. Before the
    secret exists, behavior stays backward compatible so rollout cannot lock out
    Human Authority during staging.

    Link Up is the only public-origin route allowed to ask the browser for
    camera, microphone or geolocation. This policy grants no device access by
    itself: the browser still requires an explicit user permission request, and
    the Link runtime remains fail-closed until its own gates are certified.
    """

    @app.before_request
    def _enforce_smi_gateway():
        if not _is_private_path(request.path):
            return None
        if not gateway_configured() or gateway_authorized():
            return None
        response = make_response("", 404)
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        return response

    @app.after_request
    def _scope_link_device_permissions(response):
        clean_path = request.path.rstrip("/") or "/"
        if clean_path in _LINK_DEVICE_PATHS:
            response.headers["Permissions-Policy"] = _LINK_PERMISSIONS_POLICY
        return response
