"""Human Authority approval receipts bound to exact Founder tool ActionPlans.

This reuses the production approval signing key, Human Authority identity check and
audit chain. It does not execute tools. Execution remains a later Kernel/Builder gate.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timedelta, timezone

from . import approval_service, authority, postgres_db

_ALLOWED_DECISIONS = frozenset({"APPROVED", "REJECTED"})
_ALLOWED_ACTIONS = frozenset({
    "github.branch.create",
    "github.file.write",
    "github.pr.create",
})


def record_action_decision(*, request_id: object, identity_id: object, decision: object, action_type: object, action_digest: object, ttl_seconds: int = 900) -> dict[str, object]:
    """Sign one exact Founder tool plan; never grant execution directly."""
    try:
        request_value = str(uuid.UUID(str(request_id)))
        identity_value = str(uuid.UUID(str(identity_id)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError("invalid_action_approval_identity_or_request") from exc
    decision_value = str(decision or "").strip().upper()
    action_value = str(action_type or "").strip()
    digest_value = str(action_digest or "").strip().lower()
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
    content_hash = hashlib.sha256((action_value + "|" + digest_value).encode("utf-8")).hexdigest()

    with postgres_db.connect() as connection:
        authority_record = authority.require_human_authority(connection, identity_value)
        if int(authority_record["authority_level"]) != 0:
            raise authority.HumanAuthorityRequired("human_authority_level_required")

        existing = connection.execute(
            "SELECT identity_id,task_type,content_hash FROM smi_memory_records WHERE request_id=%s",
            (request_value,),
        ).fetchone()
        if existing is None:
            connection.execute(
                """INSERT INTO smi_memory_records(
                       request_id,identity_id,task_type,content_hash,summary,
                       output_state,signal_level,rationale_json,processing_states_json)
                   VALUES (%s,%s,'FOUNDER_TOOL',%s,%s,'REVIEW_REQUIRED','YELLOW',%s::jsonb,%s::jsonb)""",
                (
                    request_value,
                    identity_value,
                    content_hash,
                    f"Founder tool proposal: {action_value}",
                    json.dumps(["Exact ActionPlan digest bound before Human Authority approval."]),
                    json.dumps(["RECEIVED","IDENTITY_VERIFIED","SMI_REVIEWED","GUARDIAN_PASSED","HUMAN_REVIEW_REQUIRED"]),
                ),
            )
        elif str(existing[0]) != identity_value or str(existing[1]) != "FOUNDER_TOOL" or str(existing[2]) != content_hash:
            raise PermissionError("request_id_conflicts_with_existing_record")

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
                   expires_at,action_digest,authority_level,nonce,signature)
               VALUES (%s,%s,%s,%s,%s,%s,%s,0,%s,%s)""",
            (receipt_id,request_value,identity_value,decision_value,issued_at,expires_at,digest_value,nonce,signature),
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
