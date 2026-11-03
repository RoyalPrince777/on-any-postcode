"""Fail-closed identity adapter for future OAP Drive integration.

Not an HTTP endpoint. Authentication must be verified by the existing Neon Auth
bridge before constructing a principal; never accept owner IDs from client input.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from oap.cloud_private_store import CloudAccessError, PrivateObjectStore


@dataclass(frozen=True)
class VerifiedDrivePrincipal:
    owner_id: str


def principal_from_verified_session(payload: Any) -> VerifiedDrivePrincipal:
    """Accept only the validated server-side Auth bridge's session response.

    The caller MUST obtain payload from neon_auth.get_session, never request JSON,
    browser claims, or a client-provided identity header.
    """
    if not isinstance(payload, Mapping):
        raise CloudAccessError("verified session required")
    session = payload.get("session")
    user = payload.get("user")
    if not isinstance(session, Mapping) or not isinstance(user, Mapping):
        raise CloudAccessError("verified session required")
    session_id = session.get("id")
    owner_id = user.get("id")
    if not isinstance(session_id, str) or not session_id.strip():
        raise CloudAccessError("verified session required")
    if not isinstance(owner_id, str) or not owner_id.strip():
        raise CloudAccessError("verified owner required")
    return VerifiedDrivePrincipal(owner_id=owner_id)


class PrivateDrive:
    """Only accepts a server-created verified principal; no public publishing."""

    def __init__(self, store: PrivateObjectStore):
        self.store = store

    def put(self, principal: VerifiedDrivePrincipal, data: bytes) -> str:
        if not isinstance(principal, VerifiedDrivePrincipal):
            raise CloudAccessError("verified principal required")
        return self.store.put(
            owner_id=principal.owner_id,
            authenticated_owner_id=principal.owner_id,
            data=data,
        )

    def get(self, principal: VerifiedDrivePrincipal, object_id: str) -> bytes:
        if not isinstance(principal, VerifiedDrivePrincipal):
            raise CloudAccessError("verified principal required")
        return self.store.get(
            owner_id=principal.owner_id,
            authenticated_owner_id=principal.owner_id,
            object_id=object_id,
        )
