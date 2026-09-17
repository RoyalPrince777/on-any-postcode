"""Provider-neutral eSIM provisioning lifecycle.

This module intentionally does not fake carrier success. A real provider adapter must
be supplied before provisioning can move beyond an approved request. Consequential
operations remain explicit and auditable.
"""
from __future__ import annotations

import dataclasses
import datetime
import typing
import uuid


TERMINAL_STATES = {"revoked", "failed"}
ALLOWED_TRANSITIONS = {
    "requested": {"approved", "revoked"},
    "approved": {"provisioning", "revoked"},
    "provisioning": {"active", "failed", "revoked"},
    "active": {"suspended", "revoked"},
    "suspended": {"active", "revoked"},
    "revoked": set(),
    "failed": set(),
}


def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


class EsimProvider(typing.Protocol):
    """Minimal contract a real eSIM provider integration must implement."""

    name: str

    def provision(self, *, request_id: str, subject_id: str) -> dict: ...
    def suspend(self, *, provider_profile_id: str) -> dict: ...
    def resume(self, *, provider_profile_id: str) -> dict: ...
    def revoke(self, *, provider_profile_id: str) -> dict: ...


@dataclasses.dataclass
class EsimRequest:
    request_id: str
    subject_id: str
    purpose: str
    state: str
    created_at: str
    updated_at: str
    approved_by: str | None = None
    provider_name: str | None = None
    provider_profile_id: str | None = None
    last_error: str | None = None


class EsimProvisioningCore:
    """Small deterministic lifecycle with human approval and fail-closed execution."""

    def __init__(self, provider: EsimProvider | None = None) -> None:
        self.provider = provider
        self._requests: dict[str, EsimRequest] = {}
        self._events: list[dict] = []

    def request(self, *, subject_id: str, purpose: str) -> dict:
        subject_id = str(subject_id or "").strip()
        purpose = str(purpose or "").strip()
        if not subject_id:
            raise ValueError("subject_id_required")
        if not purpose:
            raise ValueError("purpose_required")
        now = _now()
        item = EsimRequest(
            request_id=f"esim_{uuid.uuid4().hex}",
            subject_id=subject_id,
            purpose=purpose[:160],
            state="requested",
            created_at=now,
            updated_at=now,
        )
        self._requests[item.request_id] = item
        self._record(item, "requested")
        return dataclasses.asdict(item)

    def approve(self, request_id: str, *, founder_identity: str) -> dict:
        founder_identity = str(founder_identity or "").strip()
        if not founder_identity:
            raise PermissionError("founder_approval_required")
        item = self._get(request_id)
        self._transition(item, "approved")
        item.approved_by = founder_identity
        self._record(item, "approved", actor=founder_identity)
        return dataclasses.asdict(item)

    def provision(self, request_id: str) -> dict:
        item = self._get(request_id)
        if item.state != "approved" or not item.approved_by:
            raise PermissionError("approved_request_required")
        if self.provider is None:
            raise RuntimeError("esim_provider_not_configured")
        self._transition(item, "provisioning")
        self._record(item, "provisioning", provider=self.provider.name)
        try:
            result = self.provider.provision(
                request_id=item.request_id,
                subject_id=item.subject_id,
            )
            profile_id = str(result.get("provider_profile_id") or "").strip()
            if not profile_id or result.get("active") is not True:
                raise RuntimeError("provider_activation_not_confirmed")
            item.provider_name = self.provider.name
            item.provider_profile_id = profile_id
            self._transition(item, "active")
            self._record(item, "active", provider=self.provider.name)
            return dataclasses.asdict(item)
        except Exception as exc:
            item.last_error = type(exc).__name__
            self._transition(item, "failed")
            self._record(item, "failed", provider=self.provider.name)
            raise

    def suspend(self, request_id: str) -> dict:
        item = self._get(request_id)
        provider = self._require_provider_profile(item)
        if item.state != "active":
            raise ValueError("active_profile_required")
        result = provider.suspend(provider_profile_id=item.provider_profile_id or "")
        if result.get("suspended") is not True:
            raise RuntimeError("provider_suspend_not_confirmed")
        self._transition(item, "suspended")
        self._record(item, "suspended", provider=provider.name)
        return dataclasses.asdict(item)

    def resume(self, request_id: str) -> dict:
        item = self._get(request_id)
        provider = self._require_provider_profile(item)
        if item.state != "suspended":
            raise ValueError("suspended_profile_required")
        result = provider.resume(provider_profile_id=item.provider_profile_id or "")
        if result.get("active") is not True:
            raise RuntimeError("provider_resume_not_confirmed")
        self._transition(item, "active")
        self._record(item, "active", provider=provider.name)
        return dataclasses.asdict(item)

    def revoke(self, request_id: str) -> dict:
        item = self._get(request_id)
        if item.state in TERMINAL_STATES:
            return dataclasses.asdict(item)
        if item.provider_profile_id:
            provider = self._require_provider_profile(item)
            result = provider.revoke(provider_profile_id=item.provider_profile_id)
            if result.get("revoked") is not True:
                raise RuntimeError("provider_revoke_not_confirmed")
        self._transition(item, "revoked")
        self._record(item, "revoked", provider=item.provider_name)
        return dataclasses.asdict(item)

    def get(self, request_id: str) -> dict:
        return dataclasses.asdict(self._get(request_id))

    def events(self, request_id: str) -> list[dict]:
        self._get(request_id)
        return [dict(event) for event in self._events if event["request_id"] == request_id]

    def _get(self, request_id: str) -> EsimRequest:
        try:
            return self._requests[request_id]
        except KeyError as exc:
            raise KeyError("esim_request_not_found") from exc

    def _transition(self, item: EsimRequest, state: str) -> None:
        if state not in ALLOWED_TRANSITIONS.get(item.state, set()):
            raise ValueError(f"invalid_esim_transition:{item.state}->{state}")
        item.state = state
        item.updated_at = _now()

    def _require_provider_profile(self, item: EsimRequest) -> EsimProvider:
        if self.provider is None:
            raise RuntimeError("esim_provider_not_configured")
        if not item.provider_profile_id:
            raise RuntimeError("provider_profile_missing")
        return self.provider

    def _record(self, item: EsimRequest, event: str, **extra: str | None) -> None:
        payload = {
            "request_id": item.request_id,
            "event": event,
            "state": item.state,
            "recorded_at": _now(),
        }
        payload.update({key: value for key, value in extra.items() if value is not None})
        self._events.append(payload)


CORE = EsimProvisioningCore()
