"""Network-facing boundary between public OAP and private Founder surfaces."""
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
    return len(os.environ.get("OAP_SMI_GATEWAY_SECRET", "").strip()) >= 32


def gateway_authorized() -> bool:
    expected = os.environ.get("OAP_SMI_GATEWAY_SECRET", "").strip()
    supplied = request.headers.get(_GATEWAY_HEADER, "")
    return (
        len(expected) >= 32
        and bool(supplied)
        and hmac.compare_digest(expected, supplied)
    )


def _is_private_path(path: str) -> bool:
    clean = path.rstrip("/") or "/"
    return any(
        clean == prefix or clean.startswith(prefix + "/")
        for prefix in _PRIVATE_PATH_PREFIXES
    )


def _private_not_found():
    response = make_response("", 404)
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    return response


def register(app: Flask) -> None:
    """Keep Founder routes absent from normal public-origin access.

    Private paths always fail closed unless the dedicated private gateway sends
    the configured high-entropy gateway credential. There is no staging or
    missing-secret bypass: an absent/malformed secret means Founder routes remain
    404 on the public origin.
    """
    from . import pulse_routes

    pulse_routes.register(app)

    @app.before_request
    def _enforce_private_origin_boundary():
        if not _is_private_path(request.path):
            return None
        if gateway_authorized():
            return None
        return _private_not_found()

    @app.after_request
    def _scope_link_device_permissions(response):
        clean_path = request.path.rstrip("/") or "/"
        if clean_path in _LINK_DEVICE_PATHS:
            response.headers["Permissions-Policy"] = _LINK_PERMISSIONS_POLICY
        return response
