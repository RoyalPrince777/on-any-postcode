"""Small, first-party bridge to Managed Neon Auth.

The browser only talks to the OAP origin. Founder authentication may be served
from the Render-local verifier once it has been explicitly bound; other managed
identity traffic continues to use Neon Auth.
"""

from __future__ import annotations

import hmac
import json
import os
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from http import HTTPStatus
from typing import Any, Final
from urllib import error as urlerror
from urllib import parse as urlparse
from urllib import request as urlrequest

from . import founder_local_auth

AUTH_COOKIE_NAMES_SESSION_KEY: Final = "oap_neon_auth_cookie_names"
AUTH_TIMEOUT_SECONDS: Final = 8
MAX_AUTH_RESPONSE_BYTES: Final = 64 * 1024
MAX_COOKIE_HEADER_BYTES: Final = 16 * 1024
_COOKIE_NAME = re.compile(r"^[!#$%&'*+\-.^_`|~0-9A-Za-z]+$")
_ALLOWED_PATHS: Final = frozenset(
    {"/get-session", "/sign-in/email", "/sign-out", "/sign-up/email"}
)


class AuthUnavailable(RuntimeError):
    """Raised when the configured Auth service cannot provide a safe answer."""


@dataclass(frozen=True)
class AuthResult:
    """Bounded response from one allowlisted authentication endpoint."""

    status_code: int
    payload: Any
    set_cookie_headers: tuple[str, ...] = ()


def base_url() -> str:
    """Return the configured branch-specific Neon Auth URL."""

    return os.environ.get("NEON_AUTH_BASE_URL", "").strip().rstrip("/")


def status() -> dict[str, bool]:
    """Return a non-networked, non-sensitive Auth configuration check."""

    value = base_url()
    parsed = urlparse.urlparse(value)
    valid = (
        bool(value)
        and parsed.scheme == "https"
        and bool(parsed.hostname)
        and parsed.path.endswith("/auth")
        and not parsed.username
        and not parsed.password
        and not parsed.query
        and not parsed.fragment
    )
    return {"configured": bool(value), "valid": valid}


def founder_email_allowed(email: object) -> bool:
    """Match the configured private Founder email without disclosing it."""

    expected = os.environ.get("OAP_HUMAN_AUTHORITY_EMAIL", "").strip().casefold()
    candidate = str(email or "").strip().casefold()
    return bool(expected and candidate) and hmac.compare_digest(expected, candidate)


def configured_founder_email() -> str:
    """Return the server-side private Auth selector; never render it."""

    return os.environ.get("OAP_HUMAN_AUTHORITY_EMAIL", "").strip().casefold()


def local_founder_ready() -> bool:
    """Return whether password-only Founder auth is safely bound locally."""

    return founder_local_auth.bound()


def configured_public_origin() -> str:
    """Return one validated server-controlled HTTPS origin for Auth mutations."""

    value = (
        os.environ.get("OAP_PUBLIC_ORIGIN", "").strip()
        or os.environ.get("RENDER_EXTERNAL_URL", "").strip()
    )
    try:
        parsed = urlparse.urlparse(value)
        _ = parsed.port
    except ValueError:
        return ""
    if not (
        value
        and parsed.scheme == "https"
        and bool(parsed.hostname)
        and not parsed.username
        and not parsed.password
        and parsed.path in {"", "/"}
        and not parsed.params
        and not parsed.query
        and not parsed.fragment
    ):
        return ""
    return value.removesuffix("/")


def _required_public_origin() -> str:
    """Require the exact application origin for every state-changing Auth call."""

    origin = configured_public_origin()
    if not origin:
        raise AuthUnavailable("public_origin_not_configured")
    return origin


def _read_json(response: Any) -> Any:
    body = response.read(MAX_AUTH_RESPONSE_BYTES + 1)
    if len(body) > MAX_AUTH_RESPONSE_BYTES:
        raise AuthUnavailable("auth_response_too_large")
    if not body:
        return None
    try:
        return json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AuthUnavailable("invalid_auth_response") from exc


def _request(
    path: str,
    *,
    method: str,
    payload: Mapping[str, object] | None = None,
    cookie_header: str | None = None,
    origin: str | None = None,
) -> AuthResult:
    if path not in _ALLOWED_PATHS:
        raise ValueError("unsupported_auth_path")
    if not status()["valid"]:
        raise AuthUnavailable("neon_auth_not_configured")

    body = None
    headers = {
        "Accept": "application/json",
        "User-Agent": "OAP-Neon-Auth-Bridge/1.0",
    }
    if payload is not None:
        body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if cookie_header:
        if len(cookie_header.encode("utf-8")) > MAX_COOKIE_HEADER_BYTES:
            raise AuthUnavailable("auth_cookie_header_too_large")
        headers["Cookie"] = cookie_header
    if origin:
        if origin != configured_public_origin():
            raise AuthUnavailable("invalid_auth_origin")
        headers["Origin"] = origin

    request = urlrequest.Request(
        f"{base_url()}{path}", data=body, headers=headers, method=method
    )
    try:
        with urlrequest.urlopen(request, timeout=AUTH_TIMEOUT_SECONDS) as response:
            return AuthResult(
                status_code=int(response.status),
                payload=_read_json(response),
                set_cookie_headers=tuple(response.headers.get_all("Set-Cookie") or ()),
            )
    except urlerror.HTTPError as exc:
        try:
            payload_value = _read_json(exc)
        except AuthUnavailable:
            payload_value = None
        return AuthResult(
            status_code=int(exc.code),
            payload=payload_value,
            set_cookie_headers=tuple(exc.headers.get_all("Set-Cookie") or ()),
        )
    except (OSError, TimeoutError, urlerror.URLError) as exc:
        raise AuthUnavailable("neon_auth_unavailable") from exc


def _local_founder_result(password: str) -> AuthResult | None:
    if not founder_local_auth.bound():
        return None
    try:
        valid = founder_local_auth.verify(password)
    except founder_local_auth.FounderLocalAuthUnavailable as exc:
        raise AuthUnavailable("founder_local_auth_unavailable") from exc
    if not valid:
        return AuthResult(status_code=401, payload={"code": "INVALID_PASSWORD"})
    identity_id = founder_local_auth.resolved_identity()
    email = configured_founder_email()
    try:
        session_cookie = founder_local_auth.issue_session_cookie()
    except founder_local_auth.FounderLocalAuthUnavailable as exc:
        raise AuthUnavailable("founder_local_auth_unavailable") from exc
    return AuthResult(
        status_code=200,
        payload={
            "session": {"id": "render-local-founder"},
            "user": {
                "id": identity_id,
                "name": "OAP Founder",
                "email": email,
                "emailVerified": bool(email),
            },
        },
        set_cookie_headers=(session_cookie,),
    )


def sign_in_founder(password: str) -> AuthResult:
    """Prefer the bound password-only Founder verifier, then managed Auth."""

    local_result = _local_founder_result(password)
    if local_result is not None:
        return local_result
    email = configured_founder_email()
    if not email:
        raise AuthUnavailable("founder_selector_not_configured")
    return _request(
        "/sign-in/email",
        method="POST",
        payload={"email": email, "password": password, "rememberMe": True},
        origin=_required_public_origin(),
    )


def sign_in(email: str, password: str) -> AuthResult:
    if founder_email_allowed(email) or (
        not str(email or "").strip() and local_founder_ready()
    ):
        return sign_in_founder(password)
    return _request(
        "/sign-in/email",
        method="POST",
        payload={"email": email, "password": password, "rememberMe": True},
        origin=_required_public_origin(),
    )


def sign_up_founder(password: str, name: str) -> AuthResult:
    """Create only the server-configured private Founder identity in Managed Auth."""

    email = configured_founder_email()
    if not email:
        raise AuthUnavailable("founder_selector_not_configured")
    return _request(
        "/sign-up/email",
        method="POST",
        payload={"name": name, "email": email, "password": password},
        origin=_required_public_origin(),
    )


def get_session(cookie_header: str) -> AuthResult:
    try:
        local_user = founder_local_auth.session_user(cookie_header)
    except founder_local_auth.FounderLocalAuthUnavailable:
        local_user = None
    if local_user is not None:
        return AuthResult(
            status_code=200,
            payload={"session": {"id": "render-local-founder"}, "user": local_user},
        )
    return _request(
        "/get-session", method="GET", cookie_header=cookie_header or None
    )


def sign_out(cookie_header: str) -> AuthResult:
    if founder_local_auth.COOKIE_NAME in str(cookie_header or ""):
        return AuthResult(
            status_code=200,
            payload={"ok": True},
            set_cookie_headers=(founder_local_auth.clear_session_cookie(),),
        )
    return _request(
        "/sign-out",
        method="POST",
        cookie_header=cookie_header or None,
        origin=_required_public_origin(),
    )


def cookie_names(set_cookie_headers: Sequence[str]) -> tuple[str, ...]:
    """Extract only syntactically safe cookie names from trusted Auth headers."""

    names: list[str] = []
    for header in set_cookie_headers:
        pair = header.split(";", 1)[0]
        name, separator, _value = pair.partition("=")
        name = name.strip()
        if separator and _COOKIE_NAME.fullmatch(name) and name not in names:
            names.append(name)
    return tuple(names[:8])


def scoped_set_cookie(header: str) -> str | None:
    """Re-scope an authentication session cookie to this first-party application."""

    parts = [part.strip() for part in header.split(";") if part.strip()]
    if not parts:
        return None
    name, separator, value = parts[0].partition("=")
    name = name.strip()
    if (
        not separator
        or not _COOKIE_NAME.fullmatch(name)
        or "\r" in value
        or "\n" in value
    ):
        return None

    retained: list[str] = []
    for attribute in parts[1:]:
        key = attribute.partition("=")[0].strip().lower()
        if key in {"expires", "max-age"} and "\r" not in attribute:
            retained.append(attribute)
    attributes = ["Path=/", "Secure", "HttpOnly", "SameSite=Lax", *retained]
    return "; ".join([f"{name}={value}", *attributes])


def cookie_header(
    cookie_names_value: object,
    request_cookies: Mapping[str, str],
    *,
    application_cookie_name: str = "session",
) -> str:
    """Build a minimal Auth Cookie header without leaking app cookies."""

    if not isinstance(cookie_names_value, (list, tuple)):
        return ""
    pairs: list[str] = []
    for raw_name in cookie_names_value[:8]:
        name = str(raw_name)
        if name == application_cookie_name or not _COOKIE_NAME.fullmatch(name):
            continue
        value = request_cookies.get(name)
        if value and not any(character in value for character in ";\r\n"):
            pairs.append(f"{name}={value}")
    value = "; ".join(pairs)
    if len(value.encode("utf-8")) > MAX_COOKIE_HEADER_BYTES:
        return ""
    return value


def successful(result: AuthResult) -> bool:
    return HTTPStatus.OK <= result.status_code < HTTPStatus.MULTIPLE_CHOICES


def temporarily_unavailable(result: AuthResult) -> bool:
    """Separate provider/database outages from rejected credentials."""

    if result.status_code in {402, 408, 425, 429} or result.status_code >= 500:
        return True
    return safe_error_code(result) in {
        "DATABASE_ERROR",
        "SERVICE_UNAVAILABLE",
        "TEMPORARILY_UNAVAILABLE",
    }


def safe_error_code(result: AuthResult) -> str:
    """Return only a bounded provider error code, never message or user data."""

    payload = result.payload
    candidates: list[object] = []
    if isinstance(payload, dict):
        candidates.append(payload.get("code"))
        nested = payload.get("error")
        if isinstance(nested, dict):
            candidates.append(nested.get("code"))
    for candidate in candidates:
        value = str(candidate or "").strip()
        if re.fullmatch(r"[A-Za-z0-9_.:-]{1,80}", value):
            return value
    return "unknown"
