"""Durable owner-scoped SIKA Security Ledger.

Reuses the canonical SIKA workspace and audit_events chain. Stores security
policy/events only; it cannot move money or alter Founder authentication.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any
from uuid import UUID, uuid4

from . import postgres_db


class SikaSecurityLedgerUnavailable(RuntimeError):
    pass


def _owner(value: object) -> str:
    try:
        return str(UUID(str(value)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError("canonical_owner_uuid_required") from exc


def _digest(payload: dict[str, object]) -> str:
    return sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()


def _read_rows(connection: Any, owner: str) -> list[tuple[Any, ...]]:
    return connection.execute(
        """SELECT record_id,title,body,created_at
           FROM oap_workspace_records
           WHERE identity_id=%s AND workspace_id='sika'
             AND status='active' AND title LIKE 'SIKA-SECURITY:%%'
           ORDER BY created_at DESC, record_id DESC""",
        (owner,),
    ).fetchall()


def history(owner_id: object, *, limit: int = 50) -> list[dict[str, object]]:
    owner = _owner(owner_id)
    safe_limit = max(1, min(int(limit), 100))
    try:
        with postgres_db.connect(readonly=True) as connection:
            rows = _read_rows(connection, owner)[:safe_limit]
    except Exception as exc:
        raise SikaSecurityLedgerUnavailable("security_ledger_read_failed") from exc
    out: list[dict[str, object]] = []
    for record_id, _title, body, created_at in rows:
        try:
            item = json.loads(str(body))
        except ValueError as exc:
            raise SikaSecurityLedgerUnavailable("security_ledger_unreadable") from exc
        if (
            not isinstance(item, dict)
            or item.get("owner_id") != owner
            or item.get("digest") != _digest({k: v for k, v in item.items() if k != "digest"})
        ):
            raise SikaSecurityLedgerUnavailable("security_ledger_tampered")
        out.append({**item, "record_id": str(record_id), "created_at": str(created_at)})
    return out


def record_authenticated_owner(
    owner_id: object,
    *,
    event_type: str,
    severity: str,
    details: dict[str, object] | None = None,
) -> dict[str, object]:
    owner = _owner(owner_id)
    kind = str(event_type or "").strip().upper()[:80]
    level = str(severity or "").strip().upper()[:24]
    if not kind:
        raise ValueError("security_event_type_required")
    if level not in {"INFO", "NOTICE", "WARNING", "HIGH", "CRITICAL"}:
        raise ValueError("valid_security_severity_required")
    event_id = str(uuid4())
    payload = {
        "event_id": event_id,
        "owner_id": owner,
        "event_type": kind,
        "severity": level,
        "details": dict(details or {}),
        "money_moved": False,
        "execution_authorised": False,
        "founder_auth_touched": False,
    }
    item = {**payload, "digest": _digest(payload)}
    body = json.dumps(item, sort_keys=True, separators=(",", ":"), allow_nan=False)
    try:
        with postgres_db.connect() as connection:
            connection.execute("SELECT pg_advisory_xact_lock(%s)", (25082513,))
            row = connection.execute(
                """INSERT INTO oap_workspace_records(
                       identity_id,workspace_id,title,body,status
                   ) VALUES (%s,'sika',%s,%s,'active')
                   RETURNING record_id""",
                (owner, f"SIKA-SECURITY:{event_id}", body),
            ).fetchone()
            record_id = str(row[0])

            connection.execute("SELECT pg_advisory_xact_lock(%s)", (25082509,))
            prior = connection.execute(
                "SELECT curr_hash FROM audit_events ORDER BY event_seq DESC LIMIT 1"
            ).fetchone()
            prev_hash = str(prior[0]) if prior else "GENESIS"
            metadata = {
                "workspace_id": "sika",
                "security_event_id": event_id,
                "record_id": record_id,
                "owner_id": owner,
                "event_type": kind,
                "severity": level,
                "digest": item["digest"],
                "execution_authorised": False,
                "founder_auth_touched": False,
            }
            canonical = json.dumps(metadata, sort_keys=True, separators=(",", ":"))
            curr_hash = sha256((prev_hash + canonical).encode()).hexdigest()
            connection.execute(
                """INSERT INTO audit_events(
                       prev_hash,curr_hash,actor_id,actor_type,authority_level,
                       action,target,reason,correlation_id,metadata
                   ) VALUES (
                       %s,%s,%s,'AUTHENTICATED_USER',NULL,
                       'SIKA_SECURITY_EVENT',%s,
                       'owner_scoped_security_event',%s,%s::jsonb
                   )""",
                (
                    prev_hash,
                    curr_hash,
                    owner,
                    f"sika_security:{event_id}",
                    event_id,
                    canonical,
                ),
            )
            connection.commit()
    except ValueError:
        raise
    except Exception as exc:
        raise SikaSecurityLedgerUnavailable("security_ledger_write_failed") from exc

    reread = history(owner, limit=1)
    if not reread or reread[0].get("event_id") != event_id:
        raise SikaSecurityLedgerUnavailable("security_ledger_readback_mismatch")
    return {**reread[0], "audit_recorded": True}


def readiness() -> dict[str, object]:
    return {
        "canonical_store_reused": True,
        "workspace_id": "sika",
        "audit_chain_reused": True,
        "owner_uuid_required": True,
        "durable_security_event_store": True,
        "standalone_public_write_enabled": False,
        "authenticated_host_required": True,
        "money_execution_enabled": False,
        "founder_auth_touched": False,
    }


def latest_state(owner_id: object) -> dict[str, object]:
    events = history(owner_id, limit=100)
    daily_limit_sika = "1000.00"
    suspicious_device = False
    beneficiaries: dict[str, dict[str, object]] = {}
    alerts: list[dict[str, object]] = []
    for item in reversed(events):
        kind = str(item.get("event_type") or "")
        details = dict(item.get("details") or {})
        if kind == "TRANSFER_LIMIT_SET":
            daily_limit_sika = str(details.get("daily_limit_sika") or daily_limit_sika)
        elif kind == "DEVICE_RISK_SET":
            suspicious_device = bool(details.get("suspicious_device"))
        elif kind == "BENEFICIARY_REGISTERED":
            beneficiary_id = str(details.get("beneficiary_id") or "").strip()
            if beneficiary_id:
                beneficiaries[beneficiary_id] = {
                    "beneficiary_id": beneficiary_id,
                    "registered_at": item.get("created_at"),
                    "cooling_off_minutes": 30,
                }
        if str(item.get("severity") or "") in {"WARNING", "HIGH", "CRITICAL"}:
            alerts.append({
                "event_id": item.get("event_id"),
                "event_type": kind,
                "severity": item.get("severity"),
                "created_at": item.get("created_at"),
            })
    return {
        "daily_limit_sika": daily_limit_sika,
        "suspicious_device": suspicious_device,
        "beneficiaries": list(beneficiaries.values()),
        "alerts": list(reversed(alerts[-20:])),
        "durable": True,
        "money_moved": False,
        "founder_auth_touched": False,
    }


def set_transfer_limit(owner_id: object, daily_limit_sika: object) -> dict[str, object]:
    from decimal import Decimal

    limit = Decimal(str(daily_limit_sika))
    if limit <= 0:
        raise ValueError("positive_daily_limit_required")
    return record_authenticated_owner(
        owner_id,
        event_type="TRANSFER_LIMIT_SET",
        severity="NOTICE",
        details={"daily_limit_sika": f"{limit:.2f}"},
    )


def register_beneficiary(owner_id: object, beneficiary_id: object) -> dict[str, object]:
    beneficiary = str(beneficiary_id or "").strip()[:120]
    if not beneficiary:
        raise ValueError("beneficiary_id_required")
    return record_authenticated_owner(
        owner_id,
        event_type="BENEFICIARY_REGISTERED",
        severity="NOTICE",
        details={"beneficiary_id": beneficiary, "cooling_off_minutes": 30},
    )


def set_device_risk(owner_id: object, suspicious_device: bool) -> dict[str, object]:
    return record_authenticated_owner(
        owner_id,
        event_type="DEVICE_RISK_SET",
        severity="HIGH" if suspicious_device else "NOTICE",
        details={"suspicious_device": bool(suspicious_device)},
    )


def beneficiary_age_minutes(owner_id: object, beneficiary_id: object) -> int:
    beneficiary = str(beneficiary_id or "").strip()[:120]
    if not beneficiary:
        raise ValueError("beneficiary_id_required")
    state = latest_state(owner_id)
    for item in state["beneficiaries"]:
        if str(item.get("beneficiary_id")) != beneficiary:
            continue
        raw = str(item.get("registered_at") or "")
        try:
            created = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError as exc:
            raise SikaSecurityLedgerUnavailable(
                "beneficiary_registration_time_unreadable"
            ) from exc
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
        age = datetime.now(timezone.utc) - created.astimezone(timezone.utc)
        return max(0, int(age.total_seconds() // 60))
    return 0


def record_reauth_result(owner_id: object, *, success: bool) -> dict[str, object]:
    return record_authenticated_owner(
        owner_id,
        event_type="REAUTH_SUCCESS" if success else "REAUTH_FAILED",
        severity="NOTICE" if success else "WARNING",
        details={"success": bool(success)},
    )


def reauth_lock_state(owner_id: object) -> dict[str, object]:
    events = history(owner_id, limit=20)
    failures = 0
    for item in events:
        kind = str(item.get("event_type") or "")
        if kind == "REAUTH_SUCCESS":
            break
        if kind == "REAUTH_FAILED":
            failures += 1
    locked = failures >= 5
    return {
        "failed_attempts_since_success": failures,
        "locked": locked,
        "threshold": 5,
        "money_moved": False,
        "founder_auth_touched": False,
    }
