"""Bounded executor for the registered SYNC_INTERNAL_RECORD action.

The executor may only change an owner-scoped workspace record status between
'draft' and 'active'. It never mutates title/body, never touches archived
records, never changes identity/authority, and never performs external,
financial or publication actions.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from collections.abc import Mapping
from typing import Any

from . import postgres_db

_ALLOWED = {"draft", "active"}
_AUDIT_ACTION = "OAP_GOVERNED_INTERNAL_RECORD_SYNC"


class ExecutionBlocked(RuntimeError):
    """The bounded internal action could not execute safely."""


def _uuid(value: object, name: str) -> str:
    try:
        return str(uuid.UUID(str(value)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError(f"invalid_{name}") from exc


def _status(value: object, name: str) -> str:
    status = str(value or "").strip().casefold()
    if status not in _ALLOWED:
        raise ValueError(f"invalid_{name}")
    return status


def _proof_hash(values: Mapping[str, object]) -> str:
    canonical = json.dumps(
        dict(values),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _validate_authorization(
    authorization: Mapping[str, object],
    *,
    identity_id: str,
) -> None:
    if authorization.get("execution_authorized") is not True:
        raise ExecutionBlocked("execution_authorization_required")
    if authorization.get("execution_performed") is not False:
        raise ExecutionBlocked("fresh_authorization_required")
    if authorization.get("authority_transferred") is not False:
        raise ExecutionBlocked("authority_transfer_forbidden")
    if authorization.get("human_authority_final") is not True:
        raise ExecutionBlocked("human_authority_required")
    if authorization.get("action_name") != "SYNC_INTERNAL_RECORD":
        raise ExecutionBlocked("registered_action_required")
    policy = authorization.get("action_policy")
    if not isinstance(policy, Mapping):
        raise ExecutionBlocked("action_policy_required")
    if policy.get("external") is not False:
        raise ExecutionBlocked("external_action_forbidden")
    if policy.get("reversible") is not True:
        raise ExecutionBlocked("reversible_action_required")
    if policy.get("authority_change") is not False:
        raise ExecutionBlocked("authority_change_forbidden")
    request_id = _uuid(authorization.get("request_id"), "request_id")
    _ = request_id
    approval = _uuid(
        authorization.get("approval_receipt_id"),
        "approval_receipt_id",
    )
    _ = approval
    owner = _uuid(identity_id, "identity_id")
    _ = owner


def execute(
    authorization: Mapping[str, object],
    *,
    identity_id: object,
    record_id: object,
    expected_status: object,
    target_status: object,
) -> dict[str, Any]:
    """Execute one reversible owner-scoped status transition and verify read-back."""

    identity = _uuid(identity_id, "identity_id")
    record = _uuid(record_id, "record_id")
    expected = _status(expected_status, "expected_status")
    target = _status(target_status, "target_status")
    if expected == target:
        raise ValueError("status_transition_required")
    _validate_authorization(authorization, identity_id=identity)

    request_id = _uuid(authorization.get("request_id"), "request_id")
    approval_receipt_id = _uuid(
        authorization.get("approval_receipt_id"),
        "approval_receipt_id",
    )
    idempotency_material = {
        "request_id": request_id,
        "record_id": record,
        "expected_status": expected,
        "target_status": target,
        "action_name": "SYNC_INTERNAL_RECORD",
    }
    idempotency_key = _proof_hash(idempotency_material)

    try:
        with postgres_db.connect() as connection:
            connection.execute(
                "SELECT pg_advisory_xact_lock(hashtext(%s))",
                (f"internal-record-sync:{record}",),
            )
            prior = connection.execute(
                """SELECT workspace_id,title,body,status
                   FROM oap_workspace_records
                   WHERE record_id=%s AND identity_id=%s
                   FOR UPDATE""",
                (record, identity),
            ).fetchone()
            if prior is None:
                raise ExecutionBlocked("owner_scoped_record_not_found")
            workspace_id = str(prior[0])
            title = str(prior[1])
            body = str(prior[2])
            current_status = str(prior[3])

            if current_status == "archived":
                raise ExecutionBlocked("archived_record_immutable")
            if current_status != expected:
                raise ExecutionBlocked("stale_record_status")

            duplicate = connection.execute(
                """SELECT metadata
                   FROM audit_events
                   WHERE action=%s AND actor_id=%s
                     AND metadata->>'idempotency_key'=%s
                   ORDER BY event_seq DESC LIMIT 1""",
                (_AUDIT_ACTION, identity, idempotency_key),
            ).fetchone()
            if duplicate is not None:
                raise ExecutionBlocked("action_already_recorded")

            update = connection.execute(
                """UPDATE oap_workspace_records
                   SET status=%s,updated_at=CURRENT_TIMESTAMP
                   WHERE record_id=%s AND identity_id=%s AND status=%s
                   RETURNING workspace_id,title,body,status""",
                (target, record, identity, expected),
            ).fetchone()
            if update is None:
                raise ExecutionBlocked("concurrent_record_change")

            after = connection.execute(
                """SELECT workspace_id,title,body,status
                   FROM oap_workspace_records
                   WHERE record_id=%s AND identity_id=%s""",
                (record, identity),
            ).fetchone()
            if after is None:
                raise ExecutionBlocked("record_readback_failed")

            content_unchanged = bool(
                str(after[0]) == workspace_id
                and str(after[1]) == title
                and str(after[2]) == body
            )
            status_verified = str(after[3]) == target
            if not content_unchanged or not status_verified:
                raise ExecutionBlocked("record_verification_failed")

            before_hash = _proof_hash(
                {
                    "workspace_id": workspace_id,
                    "title": title,
                    "body": body,
                    "status": current_status,
                }
            )
            after_hash = _proof_hash(
                {
                    "workspace_id": str(after[0]),
                    "title": str(after[1]),
                    "body": str(after[2]),
                    "status": str(after[3]),
                }
            )
            rollback_token = {
                "record_id": record,
                "expected_status": target,
                "target_status": expected,
                "before_hash": before_hash,
                "after_hash": after_hash,
            }

            connection.execute("SELECT pg_advisory_xact_lock(%s)", (24680259,))
            previous = connection.execute(
                "SELECT curr_hash FROM audit_events ORDER BY event_seq DESC LIMIT 1"
            ).fetchone()
            previous_hash = str(previous[0]) if previous else "GENESIS"
            metadata = {
                "request_id": request_id,
                "approval_receipt_id": approval_receipt_id,
                "record_id": record,
                "workspace_id": workspace_id,
                "before_status": expected,
                "after_status": target,
                "before_hash": before_hash,
                "after_hash": after_hash,
                "content_unchanged": content_unchanged,
                "status_readback_verified": status_verified,
                "reversible": True,
                "idempotency_key": idempotency_key,
                "authority_transferred": False,
                "external_side_effect": False,
                "financial_side_effect": False,
            }
            canonical = json.dumps(
                metadata,
                sort_keys=True,
                separators=(",", ":"),
            )
            current_hash = hashlib.sha256(
                (previous_hash + canonical).encode("utf-8")
            ).hexdigest()
            connection.execute(
                """INSERT INTO audit_events(
                       prev_hash,curr_hash,actor_id,actor_type,authority_level,
                       action,target,reason,correlation_id,metadata
                   ) VALUES (
                       %s,%s,%s,'HUMAN_AUTHORITY',0,%s,%s,%s,%s,%s::jsonb
                   )""",
                (
                    previous_hash,
                    current_hash,
                    identity,
                    _AUDIT_ACTION,
                    f"workspace_record:{record}",
                    "bounded_owner_scoped_internal_record_status_sync",
                    request_id,
                    canonical,
                ),
            )
            connection.commit()
    except (ValueError, ExecutionBlocked):
        raise
    except Exception as exc:
        raise ExecutionBlocked("internal_record_execution_failed") from exc

    return {
        "action_name": "SYNC_INTERNAL_RECORD",
        "request_id": request_id,
        "approval_receipt_id": approval_receipt_id,
        "record_id": record,
        "workspace_id": workspace_id,
        "before_status": expected,
        "after_status": target,
        "before_hash": before_hash,
        "after_hash": after_hash,
        "content_unchanged": True,
        "status_readback_verified": True,
        "audit_recorded": True,
        "idempotency_key": idempotency_key,
        "rollback_token": rollback_token,
        "action_performed": True,
        "evidence_proven": True,
        "external_side_effect": False,
        "financial_side_effect": False,
        "authority_transferred": False,
        "human_authority_final": True,
    }


def status() -> dict[str, object]:
    return {
        "component": "OAP Bounded Internal Record Executor",
        "registered_action": "SYNC_INTERNAL_RECORD",
        "owner_scoped": True,
        "allowed_states": tuple(sorted(_ALLOWED)),
        "body_mutation_allowed": False,
        "title_mutation_allowed": False,
        "archived_mutation_allowed": False,
        "external_side_effects_allowed": False,
        "financial_side_effects_allowed": False,
        "reversible": True,
        "readback_required": True,
        "audit_required": True,
        "human_authority_final": True,
    }
