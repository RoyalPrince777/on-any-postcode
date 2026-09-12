"""Network-facing boundary between public OAP and private Founder surfaces."""
from __future__ import annotations

import hmac
import ipaddress
import os
from urllib import parse as urlparse

from flask import Flask, Request, make_response, redirect, request

_GATEWAY_HEADER = "X-OAP-SMI-Gateway"
_CLIENT_IP_HEADER = "X-OAP-Client-IP"
_PRIVATE_GATEWAY_DEFAULT = "https://oap-smi.onrender.com"
_PRIVATE_PATH_PREFIXES = (
    "/mission",
    "/smi",
    "/war-room",
    "/alignment",
    "/auth",
    "/enter-my-world",
    "/my-world",
    "/myworld",
    "/the-spot/my-world",
    "/infrastructure",
    "/api/infrastructure",
    "/api/smi",
)
_PUBLIC_PRIVATE_HANDOFFS = {
    "/smi": "/mission/ollama",
    "/mission": "/mission/ollama",
    "/mission/smi": "/mission/ollama",
    "/mission/ollama": "/mission/ollama",
    "/war-room": "/mission/war-room",
    "/mission/war-room": "/mission/war-room",
    "/mission/isac": "/mission/isac-spatial/",
    "/mission/isac-spatial": "/mission/isac-spatial/",
    "/my-world": "/my-world",
    "/myworld": "/my-world",
}
_GATEWAY_COMPAT_REDIRECTS = {
    "/mission/smi": "/mission/ollama",
    "/mission/isac": "/mission/isac-spatial/",
}
_LINK_DEVICE_PATHS = frozenset({"/linkup"})
_LINK_PERMISSIONS_POLICY = (
    "camera=(self), microphone=(self), geolocation=(self), payment=()"
)
_SHARE_UPLOAD_PATH = "/linkup/share"
_SHARE_REQUEST_MAX_BYTES = 26 * 1024 * 1024


def _canonical_client_ip(value: object) -> str | None:
    candidate = str(value or "").strip()
    if not candidate:
        return None
    try:
        return str(ipaddress.ip_address(candidate))
    except ValueError:
        return None


def _gateway_secret_matches(value: object) -> bool:
    expected = os.environ.get("OAP_SMI_GATEWAY_SECRET", "").strip()
    supplied = str(value or "")
    return (
        len(expected) >= 32
        and bool(supplied)
        and hmac.compare_digest(expected, supplied)
    )


def _private_gateway_origin() -> str:
    value = os.environ.get("OAP_PRIVATE_SMI_ORIGIN", _PRIVATE_GATEWAY_DEFAULT).strip().rstrip("/")
    try:
        parsed = urlparse.urlparse(value)
        _ = parsed.port
    except ValueError:
        return _PRIVATE_GATEWAY_DEFAULT
    if not (
        parsed.scheme == "https"
        and bool(parsed.hostname)
        and not parsed.username
        and not parsed.password
        and parsed.path in {"", "/"}
        and not parsed.params
        and not parsed.query
        and not parsed.fragment
    ):
        return _PRIVATE_GATEWAY_DEFAULT
    return value


class OAPRequest(Request):
    """Preserve request limits and restore trusted gateway client identity.

    The dedicated SMI gateway authenticates itself with a high-entropy shared
    secret and supplies a canonical client address in ``X-OAP-Client-IP``. That
    value is applied to the WSGI environment before Werkzeug snapshots
    ``remote_addr`` so downstream Founder rate limiters key the real client
    instead of the Render gateway peer. Unauthenticated public headers are
    ignored.

    Multipart framing adds a small amount of request overhead around Share files,
    so the Share endpoint receives a 26 MB transport ceiling while the domain
    layer continues to enforce its 25 MB file limit. Every other route remains
    governed by the application's normal MAX_CONTENT_LENGTH setting.
    """

    def __init__(self, environ, populate_request=True, shallow=False):
        if _gateway_secret_matches(environ.get("HTTP_X_OAP_SMI_GATEWAY")):
            client_ip = _canonical_client_ip(environ.get("HTTP_X_OAP_CLIENT_IP"))
            if client_ip is not None:
                environ["REMOTE_ADDR"] = client_ip
        super().__init__(
            environ,
            populate_request=populate_request,
            shallow=shallow,
        )

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
    return _gateway_secret_matches(request.headers.get(_GATEWAY_HEADER, ""))


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


def _private_handoff(path: str):
    clean = path.rstrip("/") or "/"
    target = _PUBLIC_PRIVATE_HANDOFFS.get(clean)
    if target is None or request.method not in {"GET", "HEAD"}:
        return None
    response = redirect(f"{_private_gateway_origin()}{target}", code=302)
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-OAP-Private-Handoff"] = "smi-gateway"
    return response


def register(app: Flask) -> None:
    """Keep Founder routes absent from normal public-origin access.

    Production public surfaces are explicitly marked ``OAP_SURFACE_ROLE=public``.
    Exact browser-facing legacy aliases hand off to the dedicated private SMI
    gateway instead of dead-ending on a public-origin 404. All other private
    paths still fail closed. Trusted gateway traffic remains the only traffic
    allowed to render Founder surfaces on the upstream application.
    """
    from . import (
        all_intelligence_views,
        contract_compatibility,
        founder_recovery_views,
        pulse_routes,
        signal_health,
        smi_certification_routes,
        smi_event_memory,
        smi_proof_views,
    )

    app.request_class = OAPRequest
    pulse_routes.register(app)
    signal_health.register(app)
    app.register_blueprint(founder_recovery_views.bp)
    app.register_blueprint(smi_certification_routes.bp)
    app.register_blueprint(smi_proof_views.bp)
    app.register_blueprint(all_intelligence_views.bp)
    contract_compatibility.register(app)
    smi_event_memory.register(app)

    @app.before_request
    def _enforce_private_origin_boundary():
        if not _is_private_path(request.path):
            return None
        clean = request.path.rstrip("/") or "/"
        if gateway_authorized():
            compatibility_target = _GATEWAY_COMPAT_REDIRECTS.get(clean)
            if compatibility_target is not None:
                response = redirect(compatibility_target, code=302)
                response.headers["Cache-Control"] = "no-store"
                return response
            return None
        if public_surface_enforced():
            handoff = _private_handoff(clean)
            if handoff is not None:
                return handoff
        if public_surface_enforced() or gateway_configured():
            return _private_not_found()
        return None

    @app.after_request
    def _scope_link_device_permissions(response):
        clean_path = request.path.rstrip("/") or "/"
        if clean_path in _LINK_DEVICE_PATHS:
            response.headers["Permissions-Policy"] = _LINK_PERMISSIONS_POLICY
        return response
