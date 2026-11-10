"""Internal, transport-neutral read-only SMI tool dispatcher.

This is not a public MCP endpoint or OAuth implementation. Authentication MUST
be completed by a future OAP-owned, HTTPS-protected connector transport. Passing
a request object to this module does not grant authentication or Founder access.
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from . import smi_chatgpt_connector

SUPPORTED = ("smi_status", "studio_capabilities")
MAX_TOOL_NAME_LENGTH = 64


class ConnectorAccessDenied(PermissionError):
    """Fail-closed access or tool policy rejection."""


def dispatch(
    name: object,
    arguments: object,
    *,
    authenticated_founder: bool,
    studio_status: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Dispatch bounded status tools; caller must establish real Founder identity.

    No model text, bearer token, session cookie, or request parameter should be
    mapped directly to authenticated_founder. Only a verified server-side auth
    decision may supply it. This module never grants execution capabilities.
    """
    if authenticated_founder is not True:
        raise ConnectorAccessDenied("founder_authentication_required")
    if not isinstance(name, str) or len(name) > MAX_TOOL_NAME_LENGTH or name not in SUPPORTED:
        raise ConnectorAccessDenied("connector_tool_not_allowed")
    if not isinstance(arguments, dict) or arguments:
        raise ValueError("connector_arguments_must_be_empty")
    safe = smi_chatgpt_connector.safe_status(
        authorized=True,
        studio_status=dict(studio_status or {}),
    )
    if name == "smi_status":
        return safe
    return {
        "contract": safe["contract"],
        "studio_id": safe["studio_id"],
        "studio_declared": safe["studio_declared"],
        "generation_backend_proven": safe["generation_backend_proven"],
        "full_live_certificate": safe["full_live_certificate"],
        "execution_granted": False,
        "publishing_granted": False,
        "human_authority_final": True,
    }
