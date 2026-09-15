"""Render-local Founder authentication bound to the canonical Human Authority.

This module never stores a plaintext password. The existing Founder chooses the
same private password they already use while inside a proven Founder recovery
session. OAP stores one salted scrypt verifier in the primary PostgreSQL store
(Render DATABASE_URL when configured) and issues a bounded HMAC-signed session
cookie after successful verification.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from http.cookies import SimpleCookie
from typing import Final

from . import authority, postgres_db

COOKIE_NAME: Final = "oap_founder_session"
SESSION_SECONDS: Final = 12 * 60 * 60
_SCRYPT_N: Final = 2**14
_SCRYPT_R: Final = 8
_SCRYPT_P: Final = 1
_SCRYPT_DKLEN: Final = 32
_ADVISORY_LOCK: Final = 24680271


class FounderLocalAuthUnavailable(RuntimeError):
    """Raised when the Render-local Founder verifier cannot be used safely."""


def _session_secret() -> bytes:
    value = os.environ.get("OAP_SESSION_SECRET", "").strip()
    if len(value) < 32:
        raise FounderLocalAuthUnavailable("session_secret_not_configured")
    return value.encode("utf-8")


def _identity() -> str:
    value = authority.configured_identity()
    if not value:
        raise FounderLocalAuthUnavailable("human_authority_identity_not_configured")
    return value


def _derive(password: str, salt: bytes) -> bytes:
    return hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=_SCRYPT_N,
        r=_SCRYPT_R,
        p=_SCRYPT_P,
        dklen=_SCRYPT_DKLEN,
    )


def _table_exists(connection) -> bool:
    row = connection.execute(
        """SELECT 1 FROM information_schema.tables
           WHERE table_schema='public' AND table_name='oap_founder_local_auth'
           LIMIT 1"""
    ).fetchone()
    return row is not None


def bound() -> bool:
    """Return whether one Render-local Founder verifier already exists."""

    if not postgres_db.configured() or not authority.configured_identity():
        return False
    try:
        with postgres_db.connect(readonly=True) as connection:
            if not _table_exists(connection):
                return False
            row = connection.execute(
                "SELECT 1 FROM oap_founder_local_auth WHERE singleton_id=1 LIMIT 1"
            ).fetchone()
            return row is not None
    except Exception:  # noqa: BLE001 - auth readiness fails closed.
        return False


def bind_existing_password(password: str) -> str:
    """Persist one salted verifier after a separately proven Founder session."""

    if len(password) < 12 or len(password) > 128 or not password.strip():
        raise ValueError("invalid_password_length")
    identity_id = _identity()
    email = authority.configured_email()
    salt = secrets.token_bytes(16)
    verifier = _derive(password, salt)

    try:
        with postgres_db.connect() as connection:
            try:
                connection.execute("SELECT pg_advisory_xact_lock(%s)", (_ADVISORY_LOCK,))
                connection.execute(
                    """CREATE TABLE IF NOT EXISTS oap_founder_local_auth (
                           singleton_id SMALLINT PRIMARY KEY CHECK (singleton_id=1),
                           identity_id UUID NOT NULL,
                           salt_hex TEXT NOT NULL CHECK (length(salt_hex)=32),
                           verifier_hex TEXT NOT NULL CHECK (length(verifier_hex)=64),
                           created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
                           updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
                       )"""
                )
                existing = connection.execute(
                    "SELECT identity_id FROM oap_founder_local_auth WHERE singleton_id=1"
                ).fetchone()
                if existing is not None:
                    if str(existing[0]) != identity_id:
                        raise FounderLocalAuthUnavailable("founder_identity_mismatch")
                    connection.commit()
                    return "complete"

                authority.sync_authenticated_identity(
                    connection,
                    identity_id=identity_id,
                    email=email,
                    display_name="OAP Founder",
                    email_verified=bool(email),
                )
                connection.execute(
                    """INSERT INTO oap_founder_local_auth
                           (singleton_id,identity_id,salt_hex,verifier_hex)
                       VALUES (1,%s,%s,%s)""",
                    (identity_id, salt.hex(), verifier.hex()),
                )
                connection.commit()
            except Exception:
                connection.rollback()
                raise
    except FounderLocalAuthUnavailable:
        raise
    except Exception as exc:
        raise FounderLocalAuthUnavailable("founder_local_auth_store_unavailable") from exc
    return "bound"


def verify(password: str) -> bool:
    """Verify a private password against the one stored Render-local verifier."""

    if not isinstance(password, str) or len(password) > 128:
        return False
    try:
        with postgres_db.connect(readonly=True) as connection:
            if not _table_exists(connection):
                return False
            row = connection.execute(
                """SELECT identity_id,salt_hex,verifier_hex
                   FROM oap_founder_local_auth WHERE singleton_id=1"""
            ).fetchone()
    except Exception as exc:
        raise FounderLocalAuthUnavailable("founder_local_auth_store_unavailable") from exc
    if row is None or str(row[0]) != authority.configured_identity():
        return False
    try:
        salt = bytes.fromhex(str(row[1]))
        expected = bytes.fromhex(str(row[2]))
        candidate = _derive(password, salt)
    except (ValueError, TypeError) as exc:
        raise FounderLocalAuthUnavailable("founder_local_auth_record_invalid") from exc
    return hmac.compare_digest(expected, candidate)


def _b64url_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _b64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode((value + padding).encode("ascii"))


def issue_session_cookie(*, now: int | None = None) -> str:
    current = int(time.time()) if now is None else int(now)
    payload = {
        "v": 1,
        "id": _identity(),
        "iat": current,
        "exp": current + SESSION_SECONDS,
        "nonce": secrets.token_urlsafe(16),
    }
    encoded = _b64url_encode(
        json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    )
    signature = hmac.new(
        _session_secret(), encoded.encode("ascii"), hashlib.sha256
    ).hexdigest()
    token = f"{encoded}.{signature}"
    return (
        f"{COOKIE_NAME}={token}; Path=/; Secure; HttpOnly; SameSite=Lax; "
        f"Max-Age={SESSION_SECONDS}"
    )


def clear_session_cookie() -> str:
    return f"{COOKIE_NAME}=; Path=/; Secure; HttpOnly; SameSite=Lax; Max-Age=0"


def _token_from_cookie_header(cookie_header: str) -> str:
    try:
        jar = SimpleCookie()
        jar.load(cookie_header or "")
        morsel = jar.get(COOKIE_NAME)
        return str(morsel.value) if morsel is not None else ""
    except Exception:  # noqa: BLE001 - malformed cookies fail closed.
        return ""


def session_user(
    cookie_header: str, *, now: int | None = None
) -> dict[str, object] | None:
    token = _token_from_cookie_header(cookie_header)
    if not token or "." not in token:
        return None
    encoded, signature = token.rsplit(".", 1)
    expected = hmac.new(
        _session_secret(), encoded.encode("ascii"), hashlib.sha256
    ).hexdigest()
    if not hmac.compare_digest(expected, signature):
        return None
    try:
        payload = json.loads(_b64url_decode(encoded).decode("utf-8"))
        current = int(time.time()) if now is None else int(now)
        identity_id = str(payload.get("id") or "")
        issued_at = int(payload.get("iat", 0))
        expires_at = int(payload.get("exp", 0))
    except (ValueError, TypeError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    if payload.get("v") != 1 or identity_id != authority.configured_identity():
        return None
    if (
        issued_at > current + 60
        or expires_at <= current
        or expires_at > issued_at + SESSION_SECONDS
    ):
        return None
    return {
        "id": identity_id,
        "name": "OAP Founder",
        "email": authority.configured_email(),
        "emailVerified": bool(authority.configured_email()),
    }
