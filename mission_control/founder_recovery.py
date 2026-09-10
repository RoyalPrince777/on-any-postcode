"""Temporary, fail-closed Founder recovery for managed-auth outages.

This does not create a second identity and does not replace Managed Neon Auth.
A high-entropy recovery code is stored only as a SHA-256 digest in environment
configuration. Successful recovery creates a short-lived signed Flask session
that is accepted only on bounded Founder control surfaces.
"""
from __future__ import annotations

import hashlib
import hmac
import os
import re
import time
from typing import Final

from flask import session

RECOVERY_TOKEN_HASH_ENV: Final = "OAP_FOUNDER_RECOVERY_TOKEN_SHA256"
RECOVERY_EXPIRES_AT_ENV: Final = "OAP_FOUNDER_RECOVERY_EXPIRES_AT"
RECOVERY_SESSION_KEY: Final = "oap_founder_recovery"
SESSION_MAX_SECONDS: Final = 15 * 60
RECOVERY_ID: Final = "00000000-0000-4000-8000-000000000777"
_HASH_PATTERN: Final = re.compile(r"^[0-9a-f]{64}$")
_ALLOWED_PRIVATE_PREFIXES: Final = (
    "/mission",
    "/smi",
    "/war-room",
    "/alignment",
    "/infrastructure",
    "/api/infrastructure",
    "/api/smi",
)


class RecoveryUnavailable(RuntimeError):
    """Raised when the temporary Founder recovery gate is not safely active."""


def _configured_hash() -> str:
    return os.environ.get(RECOVERY_TOKEN_HASH_ENV, "").strip().casefold()


def _configured_expiry() -> int:
    value = os.environ.get(RECOVERY_EXPIRES_AT_ENV, "").strip()
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _session_secret_ready() -> bool:
    return len(os.environ.get("OAP_SESSION_SECRET", "").strip()) >= 32


def configured(*, now: int | None = None) -> bool:
    """Return true only while the server-configured recovery window is active."""

    current = int(time.time()) if now is None else int(now)
    digest = _configured_hash()
    return (
        _session_secret_ready()
        and bool(_HASH_PATTERN.fullmatch(digest))
        and _configured_expiry() > current
    )


def token_allowed(candidate: object, *, now: int | None = None) -> bool:
    """Compare a supplied recovery code against the configured digest."""

    if not configured(now=now):
        return False
    supplied = str(candidate or "")
    if len(supplied) < 32 or len(supplied) > 256:
        return False
    digest = hashlib.sha256(supplied.encode("utf-8")).hexdigest()
    return hmac.compare_digest(_configured_hash(), digest)


def begin_session(*, now: int | None = None) -> int:
    """Create one short-lived signed recovery session and return its expiry."""

    current = int(time.time()) if now is None else int(now)
    if not configured(now=current):
        raise RecoveryUnavailable("founder_recovery_not_configured")
    expires_at = min(current + SESSION_MAX_SECONDS, _configured_expiry())
    session[RECOVERY_SESSION_KEY] = {"version": 1, "expires_at": expires_at}
    session.permanent = True
    return expires_at


def clear_session() -> None:
    session.pop(RECOVERY_SESSION_KEY, None)


def session_active(*, now: int | None = None) -> bool:
    """Validate the signed recovery session and configured server window."""

    current = int(time.time()) if now is None else int(now)
    if not configured(now=current):
        clear_session()
        return False
    value = session.get(RECOVERY_SESSION_KEY)
    if not isinstance(value, dict) or value.get("version") != 1:
        return False
    try:
        expires_at = int(value.get("expires_at", 0))
    except (TypeError, ValueError):
        clear_session()
        return False
    if expires_at <= current or expires_at > _configured_expiry():
        clear_session()
        return False
    return True


def private_path_allowed(path: object) -> bool:
    """Keep recovery away from My World/profile ownership and public products."""

    clean = "/" + str(path or "").lstrip("/")
    return any(
        clean == prefix or clean.startswith(prefix + "/")
        for prefix in _ALLOWED_PRIVATE_PREFIXES
    )


def recovery_user() -> dict[str, object] | None:
    """Return a synthetic, non-persisted Founder principal for the recovery window."""

    if not session_active():
        return None
    return {
        "id": RECOVERY_ID,
        "name": "OAP Founder Recovery",
        "email": "",
        "email_verified": False,
        "recovery_founder": True,
    }
