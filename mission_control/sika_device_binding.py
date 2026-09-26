"""SIKA owner-device binding for the isolated acceptance shell.

Binds an opaque OAP owner UUID to a bank-app device label. This is process-local
acceptance state only: it does not alter Founder auth, provision eSIM, or create
production identity authority.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID


@dataclass(frozen=True)
class Binding:
    owner_id: str
    device_id: str


_BINDINGS: dict[str, Binding] = {}


def _owner(value: object) -> str:
    try:
        return str(UUID(str(value)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError("canonical_owner_uuid_required") from exc


def _device(value: object) -> str:
    device = str(value or "").strip()
    if not device or len(device) > 120:
        raise ValueError("valid_device_id_required")
    return device


def bind(owner_id: object, device_id: object) -> dict[str, Any]:
    owner = _owner(owner_id)
    device = _device(device_id)
    existing = _BINDINGS.get(owner)
    if existing is not None and existing.device_id != device:
        return {
            "bound": False,
            "reason": "owner_already_bound_to_different_device",
            "owner_id": owner,
            "device_id": existing.device_id,
            "founder_auth_touched": False,
            "production_ready": False,
        }
    reverse = next((b for b in _BINDINGS.values() if b.device_id == device and b.owner_id != owner), None)
    if reverse is not None:
        return {
            "bound": False,
            "reason": "device_already_bound_to_different_owner",
            "owner_id": owner,
            "device_id": device,
            "founder_auth_touched": False,
            "production_ready": False,
        }
    _BINDINGS[owner] = Binding(owner_id=owner, device_id=device)
    return {
        "bound": True,
        "owner_id": owner,
        "device_id": device,
        "storage": "process_local_acceptance_only",
        "founder_auth_touched": False,
        "identity_authority_changed": False,
        "esim_provisioned": False,
        "production_ready": False,
    }


def status(owner_id: object, device_id: object) -> dict[str, Any]:
    owner = _owner(owner_id)
    device = _device(device_id)
    existing = _BINDINGS.get(owner)
    matched = bool(existing and existing.device_id == device)
    return {
        "owner_id": owner,
        "device_id": device,
        "matched": matched,
        "storage": "process_local_acceptance_only",
        "durable": False,
        "hrm_recorded": False,
        "founder_auth_touched": False,
        "identity_authority_changed": False,
        "production_ready": False,
    }


def unbind(owner_id: object, device_id: object) -> dict[str, Any]:
    owner = _owner(owner_id)
    device = _device(device_id)
    existing = _BINDINGS.get(owner)
    if existing is None or existing.device_id != device:
        return {
            "unbound": False,
            "reason": "binding_not_found",
            "founder_auth_touched": False,
        }
    del _BINDINGS[owner]
    return {
        "unbound": True,
        "owner_id": owner,
        "device_id": device,
        "founder_auth_touched": False,
    }
