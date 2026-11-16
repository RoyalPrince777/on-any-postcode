"""Fail-closed OAuth protected-resource discovery contract for a future OAP MCP host.

No route, OAuth server, access tokens, credentials or network listener are created.
Metadata MUST NOT be exposed as live until a separately proven HTTPS transport
and OAuth authorization server exist.
"""
from __future__ import annotations

from urllib.parse import urlsplit

READ_SCOPE = "oap.smi.status.read"


def _origin(value: object) -> str:
    if not isinstance(value, str) or not value or value.strip() != value:
        raise ValueError("oauth_https_origin_required")
    parsed = urlsplit(value)
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path not in ("", "/")
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError("oauth_https_origin_required")
    if parsed.hostname in {"localhost", "127.0.0.1", "::1"}:
        raise ValueError("oauth_public_https_origin_required")
    return value.rstrip("/")


def protected_resource_metadata(*, resource_origin: object, authorization_server_origin: object) -> dict:
    """Generate RFC 9728 metadata for a *future* verified service.

    These URLs are operator inputs, not evidence that the services exist.
    """
    resource = _origin(resource_origin)
    auth_server = _origin(authorization_server_origin)
    return {
        "resource": f"{resource}/mission/smi/mcp",
        "authorization_servers": [auth_server],
        "scopes_supported": [READ_SCOPE],
        "bearer_methods_supported": ["header"],
    }


def requirements() -> dict:
    """Static checklist only: never claims external authorization is enabled."""
    return {
        "oauth_ready": False,
        "mcp_transport_ready": False,
        "chatgpt_connected": False,
        "required_scope": READ_SCOPE,
        "token_validation_required": (
            "signature", "issuer", "audience", "expiration",
            "scope", "founder_subject", "revocation",
        ),
        "human_authority_final": True,
        "write_access_enabled": False,
    }
