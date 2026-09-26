"""Authenticated SIKA owner-session adapter.

This is the only supported bridge from an already-authenticated OAP owner
session into durable SIKA device binding. It does not authenticate users itself
and does not touch Founder authentication.

The caller must pass a canonical owner UUID resolved server-side from the
authenticated OAP session. Public request body/query owner IDs are not trusted.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from . import sika_device_binding_store


@dataclass(frozen=True)
class AuthenticatedOwner:
    owner_id: str
    source: str = "oap_authenticated_session"


def _canonical_owner(value: object) -> str:
    try:
        return str(UUID(str(value)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError("canonical_authenticated_owner_uuid_required") from exc


def resolve(owner_id: object, *, source: str) -> AuthenticatedOwner:
    canonical = _canonical_owner(owner_id)
    if source != "oap_authenticated_session":
        raise PermissionError("untrusted_owner_identity_source")
    return AuthenticatedOwner(owner_id=canonical, source=source)


def bind(owner: AuthenticatedOwner, device_id: object) -> dict[str, Any]:
    if owner.source != "oap_authenticated_session":
        raise PermissionError("untrusted_owner_identity_source")
    result = sika_device_binding_store.bind_authenticated_owner(
        owner.owner_id,
        device_id,
    )
    return {
        **result,
        "authenticated_owner_source": owner.source,
        "caller_supplied_owner_id_trusted": False,
        "founder_auth_touched": False,
    }


def recover(owner: AuthenticatedOwner, device_id: object) -> dict[str, Any]:
    if owner.source != "oap_authenticated_session":
        raise PermissionError("untrusted_owner_identity_source")
    result = sika_device_binding_store.recover_authenticated_owner(
        owner.owner_id,
        device_id,
    )
    return {
        **result,
        "authenticated_owner_source": owner.source,
        "caller_supplied_owner_id_trusted": False,
        "founder_auth_touched": False,
    }


def status(owner: AuthenticatedOwner, device_id: object) -> dict[str, Any]:
    if owner.source != "oap_authenticated_session":
        raise PermissionError("untrusted_owner_identity_source")
    state = sika_device_binding_store.read(owner.owner_id)
    return {
        "owner_id": owner.owner_id,
        "device_id": str(device_id or "").strip(),
        "matched": bool(
            state.get("bound") and state.get("device_id") == str(device_id or "").strip()
        ),
        "durable": bool(state.get("durable")),
        "authenticated_owner_source": owner.source,
        "caller_supplied_owner_id_trusted": False,
        "founder_auth_touched": False,
    }


def readiness() -> dict[str, Any]:
    return {
        "adapter_present": True,
        "required_identity_source": "oap_authenticated_session",
        "caller_supplied_owner_id_trusted": False,
        "durable_bind_available_after_server_auth_resolution": True,
        "durable_recovery_available_after_server_auth_resolution": True,
        "standalone_public_mutation_exposed": False,
        "authenticated_host_route_software_ready": True,
        "authenticated_host_route_live_proof": False,
        "founder_auth_touched": False,
        "production_ready": False,
        "reason": "live_authenticated_host_route_and_exact_head_evidence_required",
    }
