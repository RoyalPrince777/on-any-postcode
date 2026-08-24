"""Production Human Authority decision receipts for SMI Judgement."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from . import authority, postgres_db

ALLOWED_DECISIONS = frozenset({"APPROVED", "REJECTED"})


class ApprovalUnavailable(RuntimeError):
    """Raised when a decision cannot be recorded safely."""


def _signing_key() -> bytes:
    value = os.environ.get("OAP_APPROVAL_SIGNING_KEY", "").strip()
    key = value.encode("utf-8")
    if len(key) < 32:
        raise ApprovalUnavailable("approval_signing_key_not_configured")
    return key


def _canonical_receipt(
    *,
    receipt_id: str,
    request_id: str,
    identity_id: str,
    authority_level: int,
    decision: str,
    issued_at: datetime,
    expires_at: datetime,
    nonce: str,
    action_digest: str,
) -> str:
    return "|".join(
        (
            receipt_id,
            request_id,
            identity_id,
            str(authority_level),
            decision,
            issued_at.isoformat(),
            expires_at.isoformat(),
            nonce,
            action_digest,
        )
    )


def _signature(**values: Any) -> str:
    return hmac.new(
        _signing_key(),
        _canonical_receipt(**values).encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def _write_audit(
    connection: Any,
    *,
    actor_id: str,
    action: str,
    target: str,
    reason: str,
    correlation_id: str,
    metadata: dict[str, object],
) -> None:
    """Append one redacted event using the active PostgreSQL chain format."""

    connection.execute("SELECT pg_advisory_xact_lock(%s)", (24680259,))
    previous = connection.execute(
        "SELECT curr_hash FROM audit_events ORDER BY event_seq DESC LIMIT 1"
    ).fetchone()
    previous_hash = str(previous[0]) if previous else "GENESIS"
    canonical = json.dumps(metadata, sort_keys=True, separators=(",", ":"))
    current_hash = hashlib.sha256((previous_hash + canonical).encode()).hexdigest()
    connection.execute(
        """INSERT INTO audit_events(
               prev_hash,curr_hash,actor_id,actor_type,authority_level,
               action,target,reason,correlation_id,metadata
           ) VALUES (%s,%s,%s,'HUMAN_AUTHORITY',0,%s,%s,%s,%s,%s::jsonb)""",
        (
            previous_hash,
            current_hash,
            actor_id,
            action,
            target,
            reason,
            correlation_id,
            canonical,
        ),
    )


def record_decision(
    *,
    request_id: object,
    identity_id: object,
    decision: object,
    ttl_seconds: int = 3600,
) -> dict[str, object]:
    """Record one signed, action-bound, single-request human decision."""

    try:
        request_value = str(uuid.UUID(str(request_id)))
        identity_value = str(uuid.UUID(str(identity_id)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError("invalid_approval_identity_or_request") from exc
    decision_value = str(decision or "").strip().upper()
    if decision_value not in ALLOWED_DECISIONS:
        raise ValueError("invalid_approval_decision")
    ttl = min(3600, max(30, int(ttl_seconds)))
    issued_at = datetime.now(timezone.utc)
    expires_at = issued_at + timedelta(seconds=ttl)
    receipt_id = str(uuid.uuid4())
    nonce = secrets.token_urlsafe(24)

    try:
        with postgres_db.connect() as connection:
            authority_record = authority.require_human_authority(
                connection, identity_value
            )
            recommendation = connection.execute(
                """SELECT m.summary,m.output_state,j.sections_completed,
                          j.human_decision
                   FROM smi_memory_records m
                   JOIN smi_judgement_reviews j ON j.request_id=m.request_id
                   WHERE m.request_id=%s FOR UPDATE OF j""",
                (request_value,),
            ).fetchone()
            if recommendation is None:
                raise ValueError("judgement_request_not_found")
            if int(recommendation[2]) != 5:
                raise ApprovalUnavailable("judgement_sections_incomplete")
            if recommendation[3] is not None:
                raise ValueError("human_decision_already_recorded")
            action_digest = hashlib.sha256(
                json.dumps(
                    {
                        "request_id": request_value,
                        "summary": str(recommendation[0]),
                        "output_state": str(recommendation[1]),
                        "decision": decision_value,
                        "action": "RECORD_HUMAN_DECISION",
                    },
                    sort_keys=True,
                    separators=(",", ":"),
                    ensure_ascii=False,
                ).encode("utf-8")
            ).hexdigest()
            signature_values = {
                "receipt_id": receipt_id,
                "request_id": request_value,
                "identity_id": identity_value,
                "authority_level": int(authority_record["authority_level"]),
                "decision": decision_value,
                "issued_at": issued_at,
                "expires_at": expires_at,
                "nonce": nonce,
                "action_digest": action_digest,
            }
            signature = _signature(**signature_values)
            connection.execute(
                """INSERT INTO smi_approval_receipts(
                       receipt_id,request_id,identity_id,decision,issued_at,
                       expires_at,action_digest,authority_level,nonce,signature
                   ) VALUES (%s,%s,%s,%s,%s,%s,%s,0,%s,%s)""",
                (
                    receipt_id,
                    request_value,
                    identity_value,
                    decision_value,
                    issued_at,
                    expires_at,
                    action_digest,
                    nonce,
                    signature,
                ),
            )
            connection.execute(
                """UPDATE smi_judgement_reviews SET
                     human_decision=%s,human_identity_id=%s,
                     human_decided_at=%s,updated_at=CURRENT_TIMESTAMP
                   WHERE request_id=%s""",
                (decision_value, identity_value, issued_at, request_value),
            )
            action = (
                "HUMAN_APPROVED"
                if decision_value == "APPROVED"
                else "HUMAN_REJECTED"
            )
            _write_audit(
                connection,
                actor_id=identity_value,
                action=action,
                target=request_value,
                reason="Signed Human Authority Judgement decision.",
                correlation_id=request_value,
                metadata={
                    "request_id": request_value,
                    "receipt_id": receipt_id,
                    "decision": decision_value,
                    "action_digest": action_digest,
                    "authority_level": 0,
                    "execution_granted": False,
                },
            )
            connection.commit()
    except (ValueError, authority.HumanAuthorityRequired, ApprovalUnavailable):
        raise
    except Exception as exc:
        raise ApprovalUnavailable("approval_store_unavailable") from exc
    return {
        "receipt_id": receipt_id,
        "request_id": request_value,
        "decision": decision_value,
        "authority_level": 0,
        "issued_at": issued_at.isoformat(),
        "expires_at": expires_at.isoformat(),
        "signature_verified": True,
        "execution_granted": False,
    }


def _row_signature_valid(row: Any) -> bool:
    if not row or not row[8] or not row[9]:
        return False
    values = {
        "receipt_id": str(row[0]),
        "request_id": str(row[1]),
        "identity_id": str(row[2]),
        "authority_level": int(row[3]),
        "decision": str(row[4]),
        "issued_at": row[5],
        "expires_at": row[6],
        "nonce": str(row[8]),
        "action_digest": str(row[7]),
    }
    try:
        expected = _signature(**values)
    except ApprovalUnavailable:
        return False
    return hmac.compare_digest(expected, str(row[9]))


def status() -> dict[str, object]:
    """Verify the most recent receipt without disclosing receipt material."""

    result: dict[str, object] = {
        "signing_key_configured": False,
        "receipts": 0,
        "approved_receipts": 0,
        "latest_signature_valid": False,
        "latest_actionable": False,
        "ready": False,
        "error": None,
    }
    try:
        _signing_key()
        result["signing_key_configured"] = True
    except ApprovalUnavailable:
        result["error"] = "approval_signing_key_not_configured"
        return result
    try:
        with postgres_db.connect(readonly=True) as connection:
            counts = connection.execute(
                """SELECT COUNT(*),COUNT(*) FILTER (
                       WHERE decision='APPROVED' AND authority_level=0
                         AND nonce IS NOT NULL AND signature IS NOT NULL)
                   FROM smi_approval_receipts"""
            ).fetchone()
            result["receipts"] = int(counts[0])
            result["approved_receipts"] = int(counts[1])
            row = connection.execute(
                """SELECT receipt_id,request_id,identity_id,authority_level,
                          decision,issued_at,expires_at,action_digest,nonce,signature
                   FROM smi_approval_receipts
                   WHERE decision='APPROVED' AND authority_level=0
                     AND nonce IS NOT NULL
                     AND signature IS NOT NULL
                   ORDER BY issued_at DESC LIMIT 1"""
            ).fetchone()
            result["latest_signature_valid"] = _row_signature_valid(row)
            result["latest_actionable"] = bool(
                result["latest_signature_valid"]
                and row
                and row[6] > datetime.now(timezone.utc)
                and str(row[4]) == "APPROVED"
            )
    except Exception:  # noqa: BLE001
        result["error"] = "approval_store_unavailable"
    result["ready"] = bool(
        result["signing_key_configured"]
        and result["approved_receipts"]
        and result["latest_signature_valid"]
    )
    return result
