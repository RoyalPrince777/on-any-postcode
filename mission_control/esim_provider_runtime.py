"""Governed runtime attachment point for eSIM provider adapters.

No carrier is selected automatically and no credentials are read here. A concrete
adapter must be constructed by trusted application code and explicitly attached by
Founder authority before the provisioning core can call it.
"""
from __future__ import annotations

import datetime
from typing import Any

from . import esim_provisioning

_PROVIDER_STATE: dict[str, Any] = {
    "configured": False,
    "provider": None,
    "approved_by": None,
    "configured_at": None,
}


def attach_provider(
    provider: esim_provisioning.EsimProvider,
    *,
    founder_identity: str,
) -> dict[str, Any]:
    """Attach an already-constructed adapter after explicit Founder approval."""

    identity = str(founder_identity or "").strip()
    if not identity:
        raise PermissionError("founder_approval_required")
    name = str(getattr(provider, "name", "") or "").strip()
    if not name:
        raise ValueError("provider_name_required")

    configured_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
    esim_provisioning.CORE.provider = provider
    _PROVIDER_STATE.update(
        {
            "configured": True,
            "provider": name,
            "approved_by": identity,
            "configured_at": configured_at,
        }
    )
    return status()


def detach_provider(*, founder_identity: str) -> dict[str, Any]:
    """Detach the adapter so consequential carrier calls fail closed."""

    identity = str(founder_identity or "").strip()
    if not identity:
        raise PermissionError("founder_approval_required")
    esim_provisioning.CORE.provider = None
    _PROVIDER_STATE.update(
        {
            "configured": False,
            "provider": None,
            "approved_by": identity,
            "configured_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }
    )
    return status()


def status() -> dict[str, Any]:
    """Return redacted provider attachment state; never expose credentials."""

    return {
        "configured": bool(_PROVIDER_STATE["configured"]),
        "provider": _PROVIDER_STATE["provider"],
        "approved_by": _PROVIDER_STATE["approved_by"],
        "configured_at": _PROVIDER_STATE["configured_at"],
        "human_authority_final": True,
        "credentials_exposed": False,
    }
