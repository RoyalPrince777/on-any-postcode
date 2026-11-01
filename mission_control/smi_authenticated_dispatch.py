"""Internal verified-token gateway for the existing read-only SMI dispatcher.

No HTTP route, MCP listener, OAuth issuer, token storage or production access.
Transport must separately enforce HTTPS, revocation and rate limits before use.
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from . import smi_connector_dispatch, smi_mcp_token_gate


def verified_readonly_dispatch(
    *,
    bearer_token: object,
    policy: smi_mcp_token_gate.TrustedTokenPolicy,
    tool_name: object,
    arguments: object,
    studio_status: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Authenticate first, then authorize the limited read-only tool.

    The trusted policy must come from private server configuration. The caller
    must never accept it from a user-supplied body, header or model output.
    """
    smi_mcp_token_gate.verify_readonly_token(bearer_token, policy=policy)
    return smi_connector_dispatch.dispatch(
        tool_name,
        arguments,
        authenticated_founder=True,
        studio_status=studio_status,
    )
