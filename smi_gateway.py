"""Free web gateway that exposes only the private SMI surface on its own origin."""
from __future__ import annotations

import os
from collections.abc import Iterator
from urllib import error as urlerror
from urllib import parse as urlparse
from urllib import request as urlrequest

from flask import Flask, Response, make_response, redirect, request, stream_with_context

app = Flask(__name__)

_UPSTREAM_DEFAULT = "https://on-any-postcode.onrender.com"
_GATEWAY_HEADER = "X-OAP-SMI-Gateway"
_ALLOWED_REQUEST_HEADERS = {
    "accept",
    "accept-language",
    "content-type",
    "cookie",
    "last-event-id",
    "range",
    "user-agent",
    "x-oap-csrf",
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
    value = os.environ.get("OAP_PUBLIC_ORIGIN", _UPSTREAM_DEFAULT).strip()
    try:
        parsed = urlparse.urlparse(value)
        _ = parsed.port
    except ValueError as exc:
        raise RuntimeError("invalid_public_origin") from exc
    if not (
        parsed.scheme == "https"
        and parsed.hostname
        and not parsed.username
        and not parsed.password
        and parsed.path in {"", "/"}
        and not parsed.params
        and not parsed.query
        and not parsed.fragment
    ):
        raise RuntimeError("invalid_public_origin")
    return value.removesuffix("/")


def _secret() -> str:
    value = os.environ.get("OAP_SMI_GATEWAY_SECRET", "").strip()
    if len(value) < 32:
        raise RuntimeError("smi_gateway_secret_not_configured")
    return value


def _allowed(path: str) -> bool:
    clean = "/" + path.lstrip("/")
    if clean == "/auth/sign-up":
        return False
    if clean == "/mission" or clean.startswith("/mission/"):
        return True
    if clean == "/my-world" or clean.startswith("/my-world/"):
        return True
    return clean in {
        "/auth",
        "/auth/sign-in",
        "/auth/sign-out",
        "/enter-my-world",
        "/assets/oap.css",
        "/healthz",
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


def _request_headers() -> dict[str, str]:
    headers: dict[str, str] = {_GATEWAY_HEADER: _secret()}
    for name, value in request.headers.items():
        if name.casefold() in _ALLOWED_REQUEST_HEADERS:
            headers[name] = value
    return headers


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
    return redirect("/mission?mode=mission", code=302)


@app.route("/<path:path>", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"])
def gateway(path: str):
    if not _allowed(path):
        return _blocked()
    try:
        return _proxy(path)
    except RuntimeError:
        return _blocked(503)
