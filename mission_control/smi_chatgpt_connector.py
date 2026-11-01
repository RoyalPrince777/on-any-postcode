"""Read-only ChatGPT connector contract for OAP Personal SMI.

No network listener, tokens, Founder session or execution authority is created here.
The future authenticated transport may call this only after its own authorization.
"""
from __future__ import annotations

from typing import Any

CONTRACT_VERSION = "oap-smi-connector-status-v0"
ALLOWED_TOOLS = ("smi_status", "studio_capabilities", "studio_job_status", "studio_projects")
FORBIDDEN_ACTIONS = ("execute", "publish", "deploy", "distribute", "pay", "write")


def public_contract() -> dict[str, Any]:
    """Return static, non-sensitive integration metadata, not a runtime health claim."""
    return {
        "contract": CONTRACT_VERSION,
        "mode": "read_only",
        "connected": False,
        "runtime_verified": False,
        "tools_proposed": list(ALLOWED_TOOLS),
        "write_tools_enabled": False,
        "founder_authority_delegated": False,
        "human_authority_final": True,
        "provider": "first_party_oap",
        "deployment": "not_verified",
    }


def safe_status(*, authorized: bool, studio_status: dict[str, Any] | None = None) -> dict[str, Any]:
    """Allowlist response for a future *authenticated* connector transport.

    The caller must enforce authentication and Founder authorization before invoking.
    No secrets, prompts, internal URLs, private notes or raw module status escape.
    """
    if not authorized:
        raise PermissionError("founder_authorization_required")
    source = studio_status if isinstance(studio_status, dict) else {}
    return {
        "contract": CONTRACT_VERSION,
        "studio_id": "oap-studio-intelligence",
        "studio_declared": source.get("id") == "oap-studio-intelligence",
        "generation_backend_proven": source.get("generation_backend_proven") is True,
        "full_live_certificate": source.get("full_live_certificate") is True,
        "human_authority_final": True,
        "execution_granted": False,
        "publishing_granted": False,
        "deployment_proven": False,
    }
