"""Session, CSRF and bounded request-rate controls for OAP web surfaces."""

from __future__ import annotations

import hmac
import secrets
import threading
import time
import uuid
from collections import defaultdict, deque
from functools import wraps
from typing import Final

from flask import Request, current_app, g, jsonify, make_response, redirect, request, session, url_for

from . import authority, founder_recovery, neon_auth, postgres_db

IDENTITY_SESSION_KEY: Final = "oap_identity_id"
CSRF_SESSION_KEY: Final = "oap_csrf_token"
_AUTH_USER_CACHE_KEY: Final = "oap_authenticated_user"


def ensure_session_identity() -> str:
    value = session.get(IDENTITY_SESSION_KEY)
    try:
        identity_id = str(uuid.UUID(str(value)))
    except (TypeError, ValueError, AttributeError):
        identity_id = str(uuid.uuid4())
        session[IDENTITY_SESSION_KEY] = identity_id
    session.permanent = True
    return identity_id


def auth_cookie_header() -> str:
    return neon_auth.cookie_header(
        session.get(neon_auth.AUTH_COOKIE_NAMES_SESSION_KEY),
        request.cookies,
        application_cookie_name=str(current_app.config.get("SESSION_COOKIE_NAME", "session")),
    )


def current_authenticated_user() -> dict[str, object] | None:
    if _AUTH_USER_CACHE_KEY in g:
        return g.get(_AUTH_USER_CACHE_KEY)
    recovery_user = founder_recovery.recovery_user()
    if recovery_user is not None:
        setattr(g, _AUTH_USER_CACHE_KEY, recovery_user)
        return recovery_user
    header = auth_cookie_header()
    if not header:
        setattr(g, _AUTH_USER_CACHE_KEY, None)
        return None
    result = neon_auth.get_session(header)
    payload = result.payload
    if not neon_auth.successful(result) or not isinstance(payload, dict):
        setattr(g, _AUTH_USER_CACHE_KEY, None)
        return None
    user = payload.get("user")
    auth_session = payload.get("session")
    if not isinstance(user, dict) or not isinstance(auth_session, dict):
        setattr(g, _AUTH_USER_CACHE_KEY, None)
        return None
    try:
        identity_id = str(uuid.UUID(str(user.get("id"))))
    except (TypeError, ValueError, AttributeError):
        setattr(g, _AUTH_USER_CACHE_KEY, None)
        return None
    if user.get("banned") is True:
        setattr(g, _AUTH_USER_CACHE_KEY, None)
        return None
    normalized: dict[str, object] = {
        "id": identity_id,
        "name": str(user.get("name") or "OAP Member")[:120],
        "email": str(user.get("email") or "")[:320],
        "email_verified": bool(user.get("emailVerified")),
    }
    setattr(g, _AUTH_USER_CACHE_KEY, normalized)
    return normalized


def authenticated_identity() -> str:
    user = current_authenticated_user()
    if user is None:
        raise PermissionError("authentication_required")
    return str(user["id"])


def _private_error(code: str, message: str, status_code: int):
    response = make_response(jsonify(error={"code": code, "message": message}), status_code)
    response.headers["Cache-Control"] = "no-store"
    return response


def private_authority_allowed(user: dict[str, object]) -> bool:
    if user.get("recovery_founder") is True:
        return founder_recovery.session_active()
    if authority.identity_is_authority(user.get("id")):
        return True
    if bool(user.get("email_verified")) and authority.email_is_authority(user.get("email")):
        return True
    try:
        with postgres_db.connect(readonly=True) as connection:
            record = authority.authority_record(connection, user.get("id"))
    except Exception:
        return False
    return bool(record and record.get("is_human_authority"))


def login_required(*, api: bool = False, founder_only: bool = False):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            try:
                user = current_authenticated_user()
            except neon_auth.AuthUnavailable:
                if api:
                    return _private_error("authentication_unavailable", "Secure identity verification is temporarily unavailable.", 503)
                target = request.full_path.rstrip("?")
                return redirect(url_for("auth_page", next=target, auth_error="unavailable"))
            if user is None:
                if api:
                    return _private_error("authentication_required", "Sign in to access this private OAP surface.", 401)
                target = request.full_path.rstrip("?")
                return redirect(url_for("auth_page", next=target))
            if user.get("recovery_founder") is True and not founder_recovery.private_path_allowed(request.path):
                if api:
                    return _private_error("managed_identity_required", "Managed identity verification is required for this private surface.", 503)
                target = request.full_path.rstrip("?")
                return redirect(url_for("auth_page", next=target, auth_error="unavailable"))
            requires_founder = founder_only or request.blueprint == "mission_control"
            if requires_founder and not private_authority_allowed(user):
                return _private_error("human_authority_required", "This private control surface is restricted.", 403)
            return view(*args, **kwargs)
        return wrapped
    return decorator


def csrf_token() -> str:
    value = session.get(CSRF_SESSION_KEY)
    if not isinstance(value, str) or len(value) < 32:
        value = secrets.token_urlsafe(32)
        session[CSRF_SESSION_KEY] = value
    return value


def csrf_valid(request: Request) -> bool:
    expected = session.get(CSRF_SESSION_KEY)
    supplied = request.headers.get("X-OAP-CSRF") or request.form.get("csrf_token")
    return isinstance(expected, str) and isinstance(supplied, str) and hmac.compare_digest(expected, supplied)


class SlidingWindowLimiter:
    """Process-local burst shield with duplicate-request coalescing.

    Identical rapid requests from the same key are treated as one event. This keeps
    Android double taps, browser retries and proxy replay from exhausting Founder
    entry while preserving the bounded security window for distinct attempts.
    """

    def __init__(self, *, limit: int, window_seconds: int, max_keys: int = 5000, duplicate_seconds: float = 0.0):
        self.limit = limit
        self.window_seconds = window_seconds
        self.max_keys = max_keys
        self.duplicate_seconds = max(0.0, duplicate_seconds)
        self._events: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def allow(self, key: str) -> bool:
        now = time.monotonic()
        cutoff = now - self.window_seconds
        with self._lock:
            events = self._events[key]
            while events and events[0] <= cutoff:
                events.popleft()
            if events and self.duplicate_seconds and now - events[-1] < self.duplicate_seconds:
                return True
            if len(events) >= self.limit:
                return False
            events.append(now)
            if len(self._events) > self.max_keys:
                stale = [k for k, values in self._events.items() if not values or values[-1] <= cutoff]
                for stale_key in stale[: max(1, len(stale) // 2)]:
                    self._events.pop(stale_key, None)
            return True

    def reset(self) -> None:
        with self._lock:
            self._events.clear()


# Private Founder SMI chat is protected against abuse without treating an active
# conversation as an attack. Thirty requests per minute is still a hard burst cap;
# duplicate taps/retries inside one second do not consume additional limiter slots.
CHAT_BURST_LIMITER = SlidingWindowLimiter(limit=30, window_seconds=60, duplicate_seconds=1.0)
PUBLIC_WRITE_LIMITER = SlidingWindowLimiter(limit=30, window_seconds=60, duplicate_seconds=0.35)
AUTH_BURST_LIMITER = SlidingWindowLimiter(limit=10, window_seconds=15 * 60, duplicate_seconds=2.0)
