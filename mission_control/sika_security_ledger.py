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
    alert_status: dict[str, dict[str, bool]] = {}
    alert_items: list[dict[str, object]] = []
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
        elif kind in {"SECURITY_ALERT_ACK", "SECURITY_ALERT_RECOVERED", "SECURITY_ALERT_DISMISSED"}:
            target = str(details.get("security_event_id") or "")
            if target:
                state = alert_status.setdefault(
                    target, {"acknowledged": False, "recovered": False, "dismissed": False}
                )
                if kind == "SECURITY_ALERT_ACK":
                    state["acknowledged"] = True
                elif kind == "SECURITY_ALERT_RECOVERED":
                    state["recovered"] = True
                else:
                    state["dismissed"] = True
        if str(item.get("severity") or "") in {"WARNING", "HIGH", "CRITICAL"}:
            alert_items.append({
                "event_id": item.get("event_id"),
                "event_type": kind,
                "severity": item.get("severity"),
                "created_at": item.get("created_at"),
            })

    alerts: list[dict[str, object]] = []
    for item in reversed(alert_items[-20:]):
        state = alert_status.get(
            str(item.get("event_id") or ""),
            {"acknowledged": False, "recovered": False, "dismissed": False},
        )
        alerts.append({**item, **state})

    return {
        "daily_limit_sika": daily_limit_sika,
        "suspicious_device": suspicious_device,
        "beneficiaries": list(beneficiaries.values()),
        "alerts": alerts,
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


def daily_payment_activity(owner_id: object) -> dict[str, object]:
    from decimal import Decimal

    events = history(owner_id, limit=100)
    today = datetime.now(timezone.utc).date()
    attempted = Decimal(0)
    reviewed = 0
    held = 0
    for item in events:
        raw = str(item.get("created_at") or "")
        try:
            created = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            continue
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
        if created.astimezone(timezone.utc).date() != today:
            continue
        kind = str(item.get("event_type") or "")
        details = dict(item.get("details") or {})
        amount = Decimal(str(details.get("amount_sika") or "0"))
        if kind in {"PAYMENT_CONTROL_HOLD", "FRAUD_PREFLIGHT"}:
            attempted += max(amount, Decimal(0))
            reviewed += 1
        if kind == "PAYMENT_CONTROL_HOLD":
            held += 1
    return {
        "daily_attempted_sika": f"{attempted:.2f}",
        "daily_review_events": reviewed,
        "daily_hold_events": held,
        "daily_executed_spend_sika": "0.00",
        "money_execution_enabled": False,
        "truth_mode": "attempted_not_executed_spend",
    }


def create_step_up_challenge(
    owner_id: object,
    *,
    reason: str,
    amount_sika: object = "0",
) -> dict[str, object]:
    challenge_id = str(uuid4())
    issued_at = datetime.now(timezone.utc)
    expires_at = issued_at.timestamp() + 300
    receipt = record_authenticated_owner(
        owner_id,
        event_type="STEP_UP_CREATED",
        severity="WARNING",
        details={
            "challenge_id": challenge_id,
            "reason": str(reason or "security_review")[:160],
            "amount_sika": str(amount_sika),
            "status": "pending",
            "issued_at": issued_at.isoformat(),
            "expires_at_epoch": expires_at,
        },
    )
    return {
        "challenge_id": challenge_id,
        "status": "pending",
        "expires_in_seconds": 300,
        "security_receipt_id": receipt.get("event_id"),
        "money_moved": False,
        "founder_auth_touched": False,
    }


def resolve_step_up_challenge(
    owner_id: object,
    *,
    challenge_id: object,
    approved: bool,
) -> dict[str, object]:
    challenge = str(challenge_id or "").strip()
    if not challenge:
        raise ValueError("challenge_id_required")
    events = history(owner_id, limit=100)
    created = next(
        (
            item for item in events
            if item.get("event_type") == "STEP_UP_CREATED"
            and dict(item.get("details") or {}).get("challenge_id") == challenge
        ),
        None,
    )
    if created is None:
        raise ValueError("step_up_challenge_not_found")
    already = next(
        (
            item for item in events
            if item.get("event_type") == "STEP_UP_RESOLVED"
            and dict(item.get("details") or {}).get("challenge_id") == challenge
        ),
        None,
    )
    if already is not None:
        return {
            "challenge_id": challenge,
            "status": str(dict(already.get("details") or {}).get("status") or "resolved"),
            "idempotent": True,
            "replay_blocked": True,
            "money_moved": False,
            "founder_auth_touched": False,
        }

    created_details = dict(created.get("details") or {})
    expires_at_epoch = float(created_details.get("expires_at_epoch") or 0)
    expired = expires_at_epoch <= datetime.now(timezone.utc).timestamp()
    status = (
        "expired"
        if expired
        else "approved_for_review"
        if approved
        else "rejected"
    )
    receipt = record_authenticated_owner(
        owner_id,
        event_type="STEP_UP_RESOLVED",
        severity="WARNING" if expired or not approved else "NOTICE",
        details={
            "challenge_id": challenge,
            "status": status,
            "expired": expired,
            "payment_execution_authorised": False,
        },
    )
    return {
        "challenge_id": challenge,
        "status": status,
        "expired": expired,
        "security_receipt_id": receipt.get("event_id"),
        "idempotent": False,
        "replay_blocked": False,
        "money_moved": False,
        "payment_execution_authorised": False,
        "founder_auth_touched": False,
    }


def acknowledge_alert(owner_id: object, event_id: object) -> dict[str, object]:
    target = str(event_id or "").strip()
    if not target:
        raise ValueError("security_event_id_required")
    events = history(owner_id, limit=100)
    if not any(str(item.get("event_id") or "") == target for item in events):
        raise ValueError("security_event_not_found")
    receipt = record_authenticated_owner(
        owner_id,
        event_type="SECURITY_ALERT_ACK",
        severity="INFO",
        details={"security_event_id": target, "acknowledged": True},
    )
    return {
        "security_event_id": target,
        "acknowledged": True,
        "security_receipt_id": receipt.get("event_id"),
        "money_moved": False,
    }


def recover_alert(owner_id: object, event_id: object) -> dict[str, object]:
    target = str(event_id or "").strip()
    if not target:
        raise ValueError("security_event_id_required")
    events = history(owner_id, limit=100)
    if not any(str(item.get("event_id") or "") == target for item in events):
        raise ValueError("security_event_not_found")
    receipt = record_authenticated_owner(
        owner_id,
        event_type="SECURITY_ALERT_RECOVERED",
        severity="NOTICE",
        details={"security_event_id": target, "recovered": True},
    )
    return {
        "security_event_id": target,
        "recovered": True,
        "security_receipt_id": receipt.get("event_id"),
        "money_moved": False,
    }


def create_payment_intent(
    owner_id: object,
    *,
    beneficiary_id: object,
    amount_sika: object,
    reference: object = "",
) -> dict[str, object]:
    from decimal import Decimal

    owner = _owner(owner_id)
    beneficiary = str(beneficiary_id or "").strip()[:120]
    if not beneficiary:
        raise ValueError("beneficiary_id_required")
    amount = Decimal(str(amount_sika))
    if amount <= 0:
        raise ValueError("positive_amount_required")
    payment_intent_id = str(uuid4())
    receipt = record_authenticated_owner(
        owner,
        event_type="PAYMENT_INTENT_CREATED",
        severity="NOTICE",
        details={
            "payment_intent_id": payment_intent_id,
            "beneficiary_id": beneficiary,
            "amount_sika": f"{amount:.2f}",
            "reference": str(reference or "").strip()[:160],
            "status": "security_review_only",
            "payment_execution_authorised": False,
        },
    )
    return {
        "payment_intent_id": payment_intent_id,
        "beneficiary_id": beneficiary,
        "amount_sika": f"{amount:.2f}",
        "status": "security_review_only",
        "security_receipt_id": receipt.get("event_id"),
        "money_moved": False,
        "payment_execution_authorised": False,
    }


def create_step_up_for_payment_intent(
    owner_id: object,
    *,
    payment_intent_id: object,
    reason: str,
    amount_sika: object,
) -> dict[str, object]:
    intent_id = str(payment_intent_id or "").strip()
    if not intent_id:
        raise ValueError("payment_intent_id_required")
    events = history(owner_id, limit=100)
    intent = next(
        (
            item for item in events
            if item.get("event_type") == "PAYMENT_INTENT_CREATED"
            and dict(item.get("details") or {}).get("payment_intent_id") == intent_id
        ),
        None,
    )
    if intent is None:
        raise ValueError("payment_intent_not_found")
    challenge = create_step_up_challenge(
        owner_id,
        reason=reason,
        amount_sika=amount_sika,
    )
    record_authenticated_owner(
        owner_id,
        event_type="STEP_UP_PAYMENT_INTENT_LINKED",
        severity="NOTICE",
        details={
            "challenge_id": challenge["challenge_id"],
            "payment_intent_id": intent_id,
            "payment_execution_authorised": False,
        },
    )
    return {
        **challenge,
        "payment_intent_id": intent_id,
        "payment_execution_authorised": False,
    }


def bind_step_up_proof(
    owner_id: object,
    *,
    challenge_id: object,
    payment_intent_id: object,
    proof_method: object,
) -> dict[str, object]:
    challenge = str(challenge_id or "").strip()
    intent = str(payment_intent_id or "").strip()
    method = str(proof_method or "").strip().lower()
    if not challenge or not intent:
        raise ValueError("challenge_and_payment_intent_required")
    if method not in {"bank_app_password", "trusted_device_reauth"}:
        raise ValueError("unsupported_step_up_proof_method")

    events = history(owner_id, limit=100)
    linked = any(
        item.get("event_type") == "STEP_UP_PAYMENT_INTENT_LINKED"
        and dict(item.get("details") or {}).get("challenge_id") == challenge
        and dict(item.get("details") or {}).get("payment_intent_id") == intent
        for item in events
    )
    if not linked:
        raise ValueError("step_up_not_linked_to_payment_intent")

    receipt = record_authenticated_owner(
        owner_id,
        event_type="STEP_UP_PROOF_BOUND",
        severity="NOTICE",
        details={
            "challenge_id": challenge,
            "payment_intent_id": intent,
            "proof_method": method,
            "payment_execution_authorised": False,
        },
    )
    return {
        "challenge_id": challenge,
        "payment_intent_id": intent,
        "proof_method": method,
        "proof_bound": True,
        "security_receipt_id": receipt.get("event_id"),
        "payment_execution_authorised": False,
        "money_moved": False,
    }


def final_payment_review_gate(
    owner_id: object,
    *,
    challenge_id: object,
    payment_intent_id: object,
) -> dict[str, object]:
    challenge = str(challenge_id or "").strip()
    intent = str(payment_intent_id or "").strip()
    events = history(owner_id, limit=100)

    resolved = next(
        (
            item for item in events
            if item.get("event_type") == "STEP_UP_RESOLVED"
            and dict(item.get("details") or {}).get("challenge_id") == challenge
        ),
        None,
    )
    proof = next(
        (
            item for item in events
            if item.get("event_type") == "STEP_UP_PROOF_BOUND"
            and dict(item.get("details") or {}).get("challenge_id") == challenge
            and dict(item.get("details") or {}).get("payment_intent_id") == intent
        ),
        None,
    )
    linked = any(
        item.get("event_type") == "STEP_UP_PAYMENT_INTENT_LINKED"
        and dict(item.get("details") or {}).get("challenge_id") == challenge
        and dict(item.get("details") or {}).get("payment_intent_id") == intent
        for item in events
    )
    approved_for_review = bool(
        resolved
        and dict(resolved.get("details") or {}).get("status") == "approved_for_review"
    )
    allowed_to_final_review = bool(linked and proof and approved_for_review)
    return {
        "challenge_id": challenge,
        "payment_intent_id": intent,
        "linked": linked,
        "proof_bound": bool(proof),
        "approved_for_review": approved_for_review,
        "allowed_to_final_review": allowed_to_final_review,
        "payment_execution_authorised": False,
        "money_moved": False,
    }


def reauth_backoff_state(owner_id: object) -> dict[str, object]:
    events = history(owner_id, limit=50)
    failures = 0
    latest_failure_at = None
    for item in events:
        kind = str(item.get("event_type") or "")
        if kind == "REAUTH_SUCCESS":
            break
        if kind == "REAUTH_FAILED":
            failures += 1
            if latest_failure_at is None:
                latest_failure_at = str(item.get("created_at") or "")

    lock_seconds = 0
    if failures >= 7:
        lock_seconds = 900
    elif failures >= 5:
        lock_seconds = 300
    elif failures >= 3:
        lock_seconds = 60

    remaining = 0
    if lock_seconds and latest_failure_at:
        try:
            created = datetime.fromisoformat(latest_failure_at.replace("Z", "+00:00"))
            if created.tzinfo is None:
                created = created.replace(tzinfo=timezone.utc)
            elapsed = (datetime.now(timezone.utc) - created.astimezone(timezone.utc)).total_seconds()
            remaining = max(0, int(lock_seconds - elapsed))
        except ValueError:
            remaining = lock_seconds

    return {
        "failed_attempts_since_success": failures,
        "lock_seconds": lock_seconds,
        "lock_remaining_seconds": remaining,
        "locked": remaining > 0,
        "money_moved": False,
        "founder_auth_touched": False,
    }


def dismiss_alert(owner_id: object, event_id: object) -> dict[str, object]:
    target = str(event_id or "").strip()
    if not target:
        raise ValueError("security_event_id_required")
    events = history(owner_id, limit=100)
    if not any(str(item.get("event_id") or "") == target for item in events):
        raise ValueError("security_event_not_found")
    receipt = record_authenticated_owner(
        owner_id,
        event_type="SECURITY_ALERT_DISMISSED",
        severity="INFO",
        details={"security_event_id": target, "dismissed": True},
    )
    return {
        "security_event_id": target,
        "dismissed": True,
        "security_receipt_id": receipt.get("event_id"),
        "money_moved": False,
    }
