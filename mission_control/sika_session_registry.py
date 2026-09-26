"""Durable first-party SIKA bank-session and compromise registry.

This layer is separate from OAP/Founder authentication. It projects SIKA bank-app
session state from immutable owner-scoped security events and can only activate a
session for the owner's currently bound durable SIKA device.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from . import sika_device_binding_store, sika_security_ledger

SESSION_TTL_SECONDS = 15 * 60


class SikaSessionUnavailable(RuntimeError):
    pass


def _events(owner_id: object) -> list[dict[str, object]]:
    try:
        return sika_security_ledger.history(owner_id, limit=100)
    except sika_security_ledger.SikaSecurityLedgerUnavailable as exc:
        raise SikaSessionUnavailable("sika_session_history_unavailable") from exc


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _parse(value: object) -> datetime:
    raw = str(value or "")
    dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def project(owner_id: object) -> dict[str, object]:
    events = list(reversed(_events(owner_id)))
    sessions: dict[str, dict[str, object]] = {}
    compromise_locked = False
    revoked_all_at: datetime | None = None

    for item in events:
        kind = str(item.get("event_type") or "")
        details = dict(item.get("details") or {})
        created_at = str(item.get("created_at") or "")
        if kind == "SIKA_SESSION_ACTIVATED":
            sid = str(details.get("session_id") or "")
            if sid:
                sessions[sid] = {
                    "session_id": sid,
                    "device_id": str(details.get("device_id") or ""),
                    "created_at": created_at,
                    "expires_at": str(details.get("expires_at") or ""),
                    "status": "active",
                }
        elif kind == "SIKA_SESSION_REVOKED":
            sid = str(details.get("session_id") or "")
            if sid in sessions:
                sessions[sid]["status"] = "revoked"
                sessions[sid]["revoked_at"] = created_at
        elif kind == "SIKA_SESSION_REVOKE_ALL":
            try:
                revoked_all_at = _parse(created_at)
            except ValueError:
                revoked_all_at = _now()
            for session in sessions.values():
                session["status"] = "revoked"
                session["revoked_at"] = created_at
        elif kind == "SIKA_COMPROMISE_LOCK":
            compromise_locked = True
        elif kind == "SIKA_COMPROMISE_RECOVERED":
            compromise_locked = False

    now = _now()
    for session in sessions.values():
        if session.get("status") != "active":
            continue
        try:
            expires = _parse(session.get("expires_at"))
        except ValueError:
            session["status"] = "expired"
            continue
        if expires <= now:
            session["status"] = "expired"
        elif revoked_all_at is not None:
            try:
                created = _parse(session.get("created_at"))
            except ValueError:
                session["status"] = "revoked"
            else:
                if created <= revoked_all_at:
                    session["status"] = "revoked"

    active = [s for s in sessions.values() if s.get("status") == "active"]
    return {
        "sessions": list(sessions.values()),
        "active_sessions": active,
        "active_session_count": len(active),
        "compromise_locked": compromise_locked,
        "session_ttl_seconds": SESSION_TTL_SECONDS,
        "durable": True,
        "founder_auth_touched": False,
        "money_execution_enabled": False,
    }


def activate(owner_id: object, *, device_id: object) -> dict[str, object]:
    device = str(device_id or "").strip()
    if not device:
        raise ValueError("device_id_required")
    try:
        binding = sika_device_binding_store.read(owner_id)
    except sika_device_binding_store.SikaDeviceBindingUnavailable as exc:
        raise SikaSessionUnavailable("device_binding_unavailable") from exc
    if not binding.get("bound") or str(binding.get("device_id") or "") != device:
        raise ValueError("trusted_bound_device_required")

    state = project(owner_id)
    if state.get("compromise_locked"):
        raise ValueError("sika_compromise_lock_active")

    sid = str(uuid4())
    expires = _now() + timedelta(seconds=SESSION_TTL_SECONDS)
    receipt = sika_security_ledger.record_authenticated_owner(
        owner_id,
        event_type="SIKA_SESSION_ACTIVATED",
        severity="NOTICE",
        details={
            "session_id": sid,
            "device_id": device,
            "expires_at": expires.isoformat(),
            "scope": "SIKA_BANK_APP",
        },
    )
    return {
        "session_id": sid,
        "device_id": device,
        "expires_at": expires.isoformat(),
        "status": "active",
        "security_receipt_id": receipt.get("event_id"),
        "founder_auth_touched": False,
        "money_execution_enabled": False,
    }


def require_active(owner_id: object, session_id: object) -> dict[str, object]:
    sid = str(session_id or "").strip()
    if not sid:
        raise PermissionError("sika_session_required")
    state = project(owner_id)
    if state.get("compromise_locked"):
        raise PermissionError("sika_compromise_lock_active")
    session = next(
        (s for s in state["sessions"] if str(s.get("session_id")) == sid),
        None,
    )
    if session is None or session.get("status") != "active":
        raise PermissionError("sika_session_not_active")
    return session


def revoke(owner_id: object, session_id: object) -> dict[str, object]:
    session = require_active(owner_id, session_id)
    receipt = sika_security_ledger.record_authenticated_owner(
        owner_id,
        event_type="SIKA_SESSION_REVOKED",
        severity="NOTICE",
        details={
            "session_id": session["session_id"],
            "device_id": session["device_id"],
        },
    )
    return {
        "session_id": session["session_id"],
        "revoked": True,
        "security_receipt_id": receipt.get("event_id"),
        "founder_auth_touched": False,
    }


def revoke_all(owner_id: object, *, reason: str = "owner_requested") -> dict[str, object]:
    before = project(owner_id)
    receipt = sika_security_ledger.record_authenticated_owner(
        owner_id,
        event_type="SIKA_SESSION_REVOKE_ALL",
        severity="WARNING",
        details={
            "reason": str(reason or "owner_requested")[:160],
            "active_session_count_before": before["active_session_count"],
        },
    )
    return {
        "revoked_all": True,
        "active_session_count_before": before["active_session_count"],
        "security_receipt_id": receipt.get("event_id"),
        "founder_auth_touched": False,
    }


def compromise_lock(owner_id: object, *, reason: str) -> dict[str, object]:
    revoke_all(owner_id, reason="compromise_lock")
    receipt = sika_security_ledger.record_authenticated_owner(
        owner_id,
        event_type="SIKA_COMPROMISE_LOCK",
        severity="CRITICAL",
        details={"reason": str(reason or "suspected_compromise")[:160]},
    )
    return {
        "compromise_locked": True,
        "all_sessions_revoked": True,
        "security_receipt_id": receipt.get("event_id"),
        "money_execution_enabled": False,
        "founder_auth_touched": False,
    }


def recover(owner_id: object, *, trusted_device_id: object) -> dict[str, object]:
    device = str(trusted_device_id or "").strip()
    if not device:
        raise ValueError("trusted_device_id_required")
    try:
        binding = sika_device_binding_store.read(owner_id)
    except sika_device_binding_store.SikaDeviceBindingUnavailable as exc:
        raise SikaSessionUnavailable("device_binding_unavailable") from exc
    if not binding.get("bound") or str(binding.get("device_id") or "") != device:
        raise ValueError("trusted_bound_device_required")
    receipt = sika_security_ledger.record_authenticated_owner(
        owner_id,
        event_type="SIKA_COMPROMISE_RECOVERED",
        severity="NOTICE",
        details={"trusted_device_id": device},
    )
    return {
        "compromise_locked": False,
        "recovered": True,
        "trusted_device_id": device,
        "security_receipt_id": receipt.get("event_id"),
        "new_session_required": True,
        "founder_auth_touched": False,
    }
