"""Fail-closed, one-time activation for the private Founder identity.

The ceremony is intentionally narrower than public signup: the email and name
come only from trusted server configuration, and Managed Neon Auth must have no
users before the operation can run. A PostgreSQL advisory lock serialises the
final zero-user check with the provider request.
"""

from __future__ import annotations

import hmac
import logging
import os
from typing import Final, Literal

from . import neon_auth, postgres_db

ACTIVATION_TOKEN_ENV: Final = "OAP_FOUNDER_ACTIVATION_TOKEN"
MIN_ACTIVATION_TOKEN_LENGTH: Final = 32
FOUNDER_DISPLAY_NAME: Final = "OAP Founder"
_ACTIVATION_LOCK_KEY: Final = 5_322_027_026_102_513_474
LOGGER = logging.getLogger("oap.founder_activation")

ActivationState = Literal["available", "complete", "disabled", "unavailable"]
ActivationResult = Literal["activated", "complete", "rejected"]


class ActivationUnavailable(RuntimeError):
    """Raised when the one-time ceremony cannot prove a safe state."""


def _configured_token() -> str:
    return os.environ.get(ACTIVATION_TOKEN_ENV, "").strip()


def token_configured() -> bool:
    """Require a substantial code without returning or rendering its value."""

    return len(_configured_token()) >= MIN_ACTIVATION_TOKEN_LENGTH


def token_allowed(candidate: object) -> bool:
    """Compare the supplied one-time code without disclosing the configured one."""

    expected = _configured_token()
    supplied = str(candidate or "").strip()
    return (
        len(expected) >= MIN_ACTIVATION_TOKEN_LENGTH
        and bool(supplied)
        and hmac.compare_digest(expected, supplied)
    )


def _configuration_ready() -> bool:
    return (
        token_configured()
        and neon_auth.status()["valid"]
        and bool(neon_auth.configured_founder_email())
        and postgres_db.configured()
    )


def _auth_user_emails(connection) -> tuple[str, ...]:
    rows = connection.execute(
        'SELECT email FROM neon_auth."user" LIMIT 2'
    ).fetchall()
    return tuple(str(row[0] or "").strip().casefold() for row in rows)


def state() -> ActivationState:
    """Return a redacted activation state after a live, read-only user check."""

    if not token_configured():
        return "disabled"
    if not _configuration_ready():
        return "unavailable"
    try:
        with postgres_db.connect(readonly=True) as connection:
            users = _auth_user_emails(connection)
    except Exception:  # noqa: BLE001 - any uncertain dependency state fails closed.
        return "unavailable"
    return "complete" if users else "available"


def activate(password: str) -> ActivationResult:
    """Create only the configured Founder when the Auth user table is empty."""

    if not _configuration_ready():
        raise ActivationUnavailable("founder_activation_not_configured")
    try:
        with postgres_db.connect() as connection:
            connection.execute(
                "SELECT pg_advisory_xact_lock(%s)", (_ACTIVATION_LOCK_KEY,)
            )
            if _auth_user_emails(connection):
                return "complete"

            result = neon_auth.sign_up_founder(password, FOUNDER_DISPLAY_NAME)
            users = _auth_user_emails(connection)
            if (
                len(users) == 1
                and neon_auth.founder_email_allowed(users[0])
            ):
                return "activated"
            if neon_auth.successful(result):
                raise ActivationUnavailable("founder_identity_not_persisted")
            LOGGER.warning(
                "founder_activation_provider_rejected status=%s code=%s",
                result.status_code,
                neon_auth.safe_error_code(result),
            )
            return "rejected"
    except neon_auth.AuthUnavailable as exc:
        raise ActivationUnavailable("managed_auth_unavailable") from exc
    except ActivationUnavailable:
        raise
    except Exception as exc:
        raise ActivationUnavailable("founder_activation_unavailable") from exc
