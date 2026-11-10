"""Offline verification of signed JWT access tokens for a future OAP MCP transport.

No network route or token issuer. Trusted settings (public key, issuer, audience,
Founder subject) must come from server configuration, never incoming request data.
Revocation, JWKS rotation, OAuth authorization, and live transport remain separate gates.
"""
from __future__ import annotations

from dataclasses import dataclass

import jwt

from .smi_oauth_resource_contract import READ_SCOPE


class TokenRejected(PermissionError):
    """Non-disclosing authentication failure."""


@dataclass(frozen=True)
class TrustedTokenPolicy:
    issuer: str
    audience: str
    founder_subject: str
    public_key_pem: str

    def __post_init__(self):
        if not all(
            isinstance(value, str) and value.strip()
            for value in (self.issuer, self.audience, self.founder_subject, self.public_key_pem)
        ):
            raise ValueError("trusted_oauth_policy_unconfigured")


def verify_readonly_token(token: object, *, policy: TrustedTokenPolicy) -> str:
    """Verify RS256 signature and minimum required claims; return verified subject.

    This deliberately supports one pinned public key and no token-supplied JWK URL,
    key id lookup, algorithm negotiation or unverified claim-based authorisation.
    """
    if not isinstance(token, str) or not token or len(token) > 16384:
        raise TokenRejected("invalid_access_token")
    try:
        claims = jwt.decode(
            token,
            policy.public_key_pem,
            algorithms=["RS256"],
            issuer=policy.issuer,
            audience=policy.audience,
            options={"require": ["exp", "iat", "iss", "aud", "sub"]},
            leeway=0,
        )
        subject = claims.get("sub")
        scopes = claims.get("scope")
        if not isinstance(subject, str) or subject != policy.founder_subject:
            raise TokenRejected("invalid_access_token")
        if not isinstance(scopes, str) or READ_SCOPE not in scopes.split():
            raise TokenRejected("invalid_access_token")
        return subject
    except (jwt.PyJWTError, ValueError, TypeError) as exc:
        raise TokenRejected("invalid_access_token") from exc
