"""Fail-closed Identity validation without creating another identity store."""

from __future__ import annotations

from collections.abc import Iterable

from oap.contracts import IdentityRecord


class IdentityValidationError(PermissionError):
    """Raised when the canonical Identity system cannot validate a requester."""


class IdentityEngine:
    """Immutable adapter over identities supplied by the existing Identity system."""

    def __init__(self, identities: Iterable[IdentityRecord] = ()) -> None:
        records = tuple(identities)
        ids = [record.identity_id for record in records]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate Identity records are not allowed")
        for record in records:
            if not 0 <= record.authority_level <= 5:
                raise ValueError("Identity authority level must be between 0 and 5")
            if record.authority_level == 0 and record.identity_type != "human_authority":
                raise ValueError("Authority level 0 belongs only to Human Authority")
        self._records = {record.identity_id: record for record in records}

    def validate(self, identity_id: str) -> IdentityRecord:
        """Return an active identity or fail closed."""

        identity = self._records.get(identity_id)
        if identity is None:
            raise IdentityValidationError("Identity is not registered")
        if identity.status != "ACTIVE":
            raise IdentityValidationError("Identity is not active")
        return identity

    def status(self) -> dict[str, object]:
        active = sum(record.status == "ACTIVE" for record in self._records.values())
        return {
            "component": "Identity",
            "ready": bool(active),
            "registered": len(self._records),
            "active": active,
            "mode": "injected canonical records",
        }
