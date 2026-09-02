"""Human Authority approval receipts bound to exact Founder tool ActionPlans.

This reuses the production approval signing key, Human Authority identity check and
audit chain. It does not execute tools. Execution remains a later Kernel/Builder gate.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from . import approval_service, authority, postgres_db

_ALLOWED_DECISIONS = frozenset({"APPROVED", "REJECTED"})
_ALLOWED_ACTIONS = frozenset({
    "github.branch.create",
    "github.file.write",
    "github.pr.create",
})


def record_action_decision(
    *,
    request_id: object,
    identity_id: object,
    decision: object,
    action_type: object,
    action_digest: object,
    ttl_seconds: int = 900,
) -> dict[str, object]:
    """Sign one exact Founder tool plan; never grant execution directly."""

    request_value = str(request_id or "").strip()
    identity_value = str(identity_id or "").strip()
    decision_value = str(decision or "").strip().upper()
    action_value = str(action_type or "").strip()
    digest_value = str(action_digest or "").strip().lower()
    if not request_value or len(request_value) > 128:
        raise ValueError("invalid_action_request_id")
    try:
        identity_value = str(uuid.UUID(identity_value))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError("invalid_action_approval_identity") from exc
    if decision_value not in _ALLOWED_DECISIONS:
        raise ValueError("invalid_action_approval_decision")
    if action_value not in _ALLOWED_ACTIONS:
        raise ValueError("unapproved_action_type")
    if len(digest_value) != 64 or any(ch not in "0123456789abcdef" for ch in digest_value):
        raise ValueError("invalid_action_digest")

    ttl = min(1800, max(30, int(ttl_seconds)))
    issued_at = datetime.now(timezone.utc)
    expires_at = issued_at + timedelta(seconds=ttl)
    receipt_id = str(uuid.uuid4())
    nonce = uuid.uuid4().hex + uuid.uuid4().hex

    with postgres_db.connect() as connection:
        authority_record = authority.require_human_authority(connection, identity_value)
        if int(authority_record["authority_level"]) != 0:
            raise authority.HumanAuthorityRequired("human_authority_level_required")
        signature_values = {
            "receipt_id": receipt_id,
            "request_id": request_value,
            "identity_id": identity_value,
            "authority_level": 0,
            "decision": decision_value,
            "issued_at": issued_at,
            "expires_at": expires_at,
            "nonce": nonce,
            "action_digest": digest_value,
        }
        signature = approval_service._signature(**signature_values)
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
                digest_value,
                nonce,
                signature,
            ),
        )
        approval_service._write_audit(
            connection,
            actor_id=identity_value,
            action="FOUNDER_TOOL_APPROVED" if decision_value == "APPROVED" else "FOUNDER_TOOL_REJECTED",
            target=request_value,
            reason="Signed Human Authority Founder tool decision.",
            correlation_id=request_value,
            metadata={
                "request_id": request_value,
                "receipt_id": receipt_id,
                "decision": decision_value,
                "action_type": action_value,
                "action_digest": digest_value,
                "authority_level": 0,
                "execution_granted": False,
            },
        )
        connection.commit()

    return {
        "receipt_id": receipt_id,
        "request_id": request_value,
        "decision": decision_value,
        "action_type": action_value,
        "action_digest": digest_value,
        "authority_level": 0,
        "issued_at": issued_at.isoformat(),
        "expires_at": expires_at.isoformat(),
        "signature_verified": True,
        "execution_granted": False,
        "next_gate": "Living Kernel",
    }
