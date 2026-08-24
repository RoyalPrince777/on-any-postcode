"""Session, CSRF and bounded request-rate controls for OAP web surfaces."""

from __future__ import annotations

import hmac
import secrets
import threading
import time
import uuid
from collections import defaultdict, deque
from typing import Final

from flask import Request, session

IDENTITY_SESSION_KEY: Final = "oap_identity_id"
CSRF_SESSION_KEY: Final = "oap_csrf_token"


def ensure_session_identity() -> str:
    """Return one signed-session identity, replacing malformed values safely."""

    value = session.get(IDENTITY_SESSION_KEY)
    try:
        identity_id = str(uuid.UUID(str(value)))
    except (TypeError, ValueError, AttributeError):
        identity_id = str(uuid.uuid4())
        session[IDENTITY_SESSION_KEY] = identity_id
    session.permanent = True
    return identity_id


def csrf_token() -> str:
    """Return a high-entropy CSRF token stored inside the signed session."""

    value = session.get(CSRF_SESSION_KEY)
    if not isinstance(value, str) or len(value) < 32:
        value = secrets.token_urlsafe(32)
        session[CSRF_SESSION_KEY] = value
    return value


def csrf_valid(request: Request) -> bool:
    """Validate either the JSON header or conventional HTML form token."""

    expected = session.get(CSRF_SESSION_KEY)
    supplied = request.headers.get("X-OAP-CSRF") or request.form.get("csrf_token")
    return (
        isinstance(expected, str)
        and isinstance(supplied, str)
        and hmac.compare_digest(expected, supplied)
    )


class SlidingWindowLimiter:
    """A small process-local shield backed by a deterministic sliding window.

    Durable chat and community write limits are also enforced in PostgreSQL.
    This layer rejects bursts before a database or intelligence provider is used.
    """

    def __init__(self, *, limit: int, window_seconds: int, max_keys: int = 5000):
        self.limit = limit
        self.window_seconds = window_seconds
        self.max_keys = max_keys
        self._events: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def allow(self, key: str) -> bool:
        now = time.monotonic()
        cutoff = now - self.window_seconds
        with self._lock:
            events = self._events[key]
            while events and events[0] <= cutoff:
                events.popleft()
            if len(events) >= self.limit:
                return False
            events.append(now)
            if len(self._events) > self.max_keys:
                stale = [
                    item_key
                    for item_key, item_events in self._events.items()
                    if not item_events or item_events[-1] <= cutoff
                ]
                for item_key in stale[: max(1, len(stale) // 2)]:
                    self._events.pop(item_key, None)
            return True

    def reset(self) -> None:
        """Clear local limiter state; used by isolated test and worker lifecycles."""

        with self._lock:
            self._events.clear()


CHAT_BURST_LIMITER = SlidingWindowLimiter(limit=12, window_seconds=60)
PUBLIC_WRITE_LIMITER = SlidingWindowLimiter(limit=30, window_seconds=60)
