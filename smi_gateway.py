"""Free web gateway that exposes only the private SMI surface on its own origin."""
from __future__ import annotations

import ipaddress
import json
import os
from collections.abc import Iterator
from urllib import error as urlerror
from urllib import parse as urlparse
from urllib import request as urlrequest

from flask import Flask, Response, make_response, redirect, request, stream_with_context

app = Flask(__name__)

_UPSTREAM_DEFAULT = "https://on-any-postcode.onrender.com"
_GATEWAY_HEADER = "X-OAP-SMI-Gateway"
_CLIENT_IP_HEADER = "X-OAP-Client-IP"
_FOUNDER_RECOVERY_FALLBACK = "/auth/recover-founder?next=/mission/ollama"
_ALLOWED_REQUEST_HEADERS = {
    "accept",
    "accept-language",
    "content-type",
    "cookie",
    "last-event-id",
    "range",
    "user-agent",
    "x-oap-csrf",
    "x-oap-home-node-token",
}
_HOP_BY_HOP = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailer",
    "transfer-encoding",
    "upgrade",
    "content-length",
}


class _NoRedirect(urlrequest.HTTPRedirectHandler):
    """Return upstream redirects to the browser instead of following them here."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ARG002
        return None


_OPENER = urlrequest.build_opener(_NoRedirect())


def _origin() -> str:
    value = os.environ.get("OAP_PUBLIC_ORIGIN", _UPSTREAM_DEFAULT).strip().rstrip("/")
    parsed = urlparse.urlparse(value)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise RuntimeError("invalid_public_origin")
    return value


def _secret() -> str:
    value = os.environ.get("OAP_SMI_GATEWAY_SECRET", "").strip()
    if len(value) < 32:
        raise RuntimeError("smi_gateway_secret_not_configured")
    return value


def _revision() -> str:
    """Return a bounded public-safe revision fingerprint for release drift checks."""

    raw = (
        os.environ.get("RENDER_GIT_COMMIT", "").strip()
        or os.environ.get("OAP_ENV_REVISION", "").strip()
        or "unknown"
    )
    safe = "".join(character for character in raw if character.isalnum() or character in ".-_")
    if not safe:
        return "unknown"
    return safe[:12]


def _allowed(path: str) -> bool:
    clean = "/" + path.lstrip("/")
    if clean == "/auth/sign-up":
        return False
    if clean == "/mission" or clean.startswith("/mission/"):
        return True
    if clean == "/smi" or clean.startswith("/smi/"):
        return True
    if clean == "/war-room" or clean.startswith("/war-room/"):
        return True
    if clean == "/alignment" or clean.startswith("/alignment/"):
        return True
    if clean == "/my-world" or clean.startswith("/my-world/"):
        return True
    if clean == "/myworld" or clean.startswith("/myworld/"):
        return True
    if clean == "/infrastructure" or clean.startswith("/infrastructure/"):
        return True
    if clean == "/api/infrastructure" or clean.startswith("/api/infrastructure/"):
        return True
    return clean in {
        "/auth",
        "/auth/sign-in",
        "/auth/sign-out",
        "/auth/recover-founder",
        "/enter-my-world",
        "/assets/oap.css",
        "/healthz",
        "/api/smi/thinking-certification",
    }


def _blocked(status: int = 404):
    response = make_response("", status)
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    return response


def _upstream_url(path: str) -> str:
    clean = "/" + path.lstrip("/")
    query = request.query_string.decode("ascii", "ignore")
    return f"{_origin()}{clean}" + (f"?{query}" if query else "")


def _client_ip() -> str:
    """Return a canonical client IP for the trusted upstream rate-limit key.

    Render terminates public traffic before it reaches this gateway and places the
    real client address first in X-Forwarded-For. Outside Render, use the direct
    socket peer instead. Invalid or missing values fail closed to ``unknown``.
    """

    candidate = str(request.remote_addr or "").strip()
    if os.environ.get("RENDER", "").strip().casefold() == "true":
        forwarded = request.headers.get("X-Forwarded-For", "")
        first = forwarded.split(",", 1)[0].strip()
        if first:
            candidate = first
    try:
        return str(ipaddress.ip_address(candidate))
    except ValueError:
        return "unknown"


def _request_headers() -> dict[str, str]:
    headers: dict[str, str] = {
        _GATEWAY_HEADER: _secret(),
        _CLIENT_IP_HEADER: _client_ip(),
    }
    for name, value in request.headers.items():
        if name.casefold() in _ALLOWED_REQUEST_HEADERS:
            headers[name] = value
    return headers


def _auth_unavailable_fallback(path: str, status: int, headers):
    """Route only private SMI managed-auth outages into Render Founder recovery."""

    clean = "/" + path.lstrip("/")
    if clean == "/auth/sign-in" and request.method == "POST" and status == 503:
        return redirect(_FOUNDER_RECOVERY_FALLBACK, code=302)

    if status not in {301, 302, 303, 307, 308}:
        return None
    location = str(headers.get("Location") or "")
    if location.startswith(_origin()):
        location = location[len(_origin()) :] or "/"
    parsed = urlparse.urlparse(location)
    if parsed.path not in {"/auth", "/enter-my-world"}:
        return None
    query = urlparse.parse_qs(parsed.query, keep_blank_values=True)
    if query.get("auth_error") != ["unavailable"]:
        return None
    return redirect(_FOUNDER_RECOVERY_FALLBACK, code=302)


def _proxy(path: str):
    body = request.get_data(cache=False) if request.method not in {"GET", "HEAD"} else None
    upstream_request = urlrequest.Request(
        _upstream_url(path),
        data=body,
        headers=_request_headers(),
        method=request.method,
    )
    try:
        upstream = _OPENER.open(upstream_request, timeout=120)
    except urlerror.HTTPError as exc:
        upstream = exc
    except (OSError, TimeoutError, urlerror.URLError):
        return _blocked(503)

    status = int(getattr(upstream, "status", getattr(upstream, "code", 502)))
    fallback = _auth_unavailable_fallback(path, status, upstream.headers)
    if fallback is not None:
        upstream.close()
        fallback.headers["Cache-Control"] = "no-store"
        fallback.headers["X-OAP-Surface"] = "sovereign-megaverse-intelligence"
        return fallback

    def generate() -> Iterator[bytes]:
        try:
            while True:
                chunk = upstream.read(64 * 1024)
                if not chunk:
                    break
                yield chunk
        finally:
            upstream.close()

    response = Response(stream_with_context(generate()), status=status)
    for name, value in upstream.headers.items():
        lowered = name.casefold()
        if lowered in _HOP_BY_HOP or lowered == "set-cookie":
            continue
        if lowered == "location" and value.startswith(_origin()):
            value = value[len(_origin()) :] or "/"
        response.headers[name] = value
    for value in upstream.headers.get_all("Set-Cookie") or ():
        response.headers.add("Set-Cookie", value)
    response.headers["Cache-Control"] = response.headers.get("Cache-Control", "no-store")
    response.headers["X-OAP-Surface"] = "sovereign-megaverse-intelligence"
    return response


@app.get("/")
def root():
    """Enter Founder sign-in and return directly to Personal SMI."""
    return redirect("/auth?next=/mission/ollama", code=302)


@app.get("/founder")
def founder_access_alias():
    """Stable Founder bookmark; recovery mechanics remain an internal auth detail."""
    return redirect("/auth/recover-founder?next=/mission/ollama", code=302)


@app.get("/smi")
@app.get("/chat")
def personal_smi_alias():
    return redirect("/mission/ollama", code=302)


@app.get("/war-room")
def war_room_alias():
    return redirect("/mission/war-room", code=302)


@app.get("/healthz")
def healthz():
    """Report only SMI gateway process liveness; do not probe OAP World or Neon."""

    response = make_response(
        json.dumps(
            {
                "status": "ok",
                "service": "oap-smi-gateway",
                "scope": "process",
                "revision": _revision(),
            },
            separators=(",", ":"),
        )
        + "\n",
        200,
    )
    response.mimetype = "application/json"
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-OAP-Surface"] = "sovereign-megaverse-intelligence"
    response.headers["X-OAP-Health-Scope"] = "process"
    return response


@app.route("/<path:path>", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"])
def gateway(path: str):
    if not _allowed(path):
        return _blocked()
    try:
        return _proxy(path)
    except RuntimeError:
        return _blocked(503)
