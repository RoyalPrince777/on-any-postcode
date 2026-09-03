"""Network-facing boundary between public OAP and private Founder surfaces."""
from __future__ import annotations

import hmac
import os

from flask import Flask, Request, make_response, request

_GATEWAY_HEADER = "X-OAP-SMI-Gateway"
_PRIVATE_PATH_PREFIXES = (
    "/mission",
    "/auth",
    "/enter-my-world",
    "/my-world",
    "/myworld",
    "/the-spot/my-world",
    "/infrastructure",
    "/api/infrastructure",
)
_LINK_DEVICE_PATHS = frozenset({"/linkup"})
_LINK_PERMISSIONS_POLICY = (
    "camera=(self), microphone=(self), geolocation=(self), payment=()"
)
_SHARE_UPLOAD_PATH = "/linkup/share"
_SHARE_REQUEST_MAX_BYTES = 26 * 1024 * 1024


class OAPRequest(Request):
    """Preserve the global request cap while allowing 25 MB Share payloads.

    Multipart framing adds a small amount of request overhead around the file
    itself, so the Share endpoint receives a 26 MB transport ceiling while the
    domain layer continues to enforce its 25 MB file limit. Every other route
    remains governed by the application's normal MAX_CONTENT_LENGTH setting.
    """

    @property
    def max_content_length(self) -> int | None:  # type: ignore[override]
        clean_path = self.path.rstrip("/") or "/"
        if self.method == "POST" and clean_path == _SHARE_UPLOAD_PATH:
            return _SHARE_REQUEST_MAX_BYTES
        return super().max_content_length


def gateway_configured() -> bool:
    return len(os.environ.get("OAP_SMI_GATEWAY_SECRET", "").strip()) >= 32


def public_surface_enforced() -> bool:
    return os.environ.get("OAP_SURFACE_ROLE", "").strip().casefold() == "public"


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

    Production public surfaces are explicitly marked ``OAP_SURFACE_ROLE=public``
    and therefore fail closed even if their gateway secret is missing. A private
    path is reachable only when the dedicated private gateway supplies the
    configured high-entropy credential.
    """
    from . import pulse_routes

    app.request_class = OAPRequest
    pulse_routes.register(app)

    @app.before_request
    def _enforce_private_origin_boundary():
        if not _is_private_path(request.path):
            return None
        if gateway_authorized():
            return None
        if public_surface_enforced() or gateway_configured():
            return _private_not_found()
        return None

    @app.after_request
    def _scope_link_device_permissions(response):
        clean_path = request.path.rstrip("/") or "/"
        if clean_path in _LINK_DEVICE_PATHS:
            response.headers["Permissions-Policy"] = _LINK_PERMISSIONS_POLICY
        return response
