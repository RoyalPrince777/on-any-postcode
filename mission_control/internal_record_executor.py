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

from . import governed_action_pipeline, postgres_db

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


def _governance_checks(
    authorization: Mapping[str, object],
    *,
    owner_scope_verified: bool,
    status_readback_verified: bool,
    content_unchanged: bool,
    audit_recorded: bool,
    rollback_ready: bool,
) -> dict[str, dict[str, bool]]:
    """Map concrete executor evidence to the canonical 7-7-7 checks."""

    policy = authorization.get("action_policy")
    policy = policy if isinstance(policy, Mapping) else {}
    signed_approval_present = bool(authorization.get("approval_receipt_id"))
    canonical_stages = tuple(authorization.get("stages") or ())
    return {
        "mind": {
            "evidence": bool(status_readback_verified and content_unchanged),
            "context": bool(owner_scope_verified),
            "intelligence": bool(
                authorization.get("action_name") == "SYNC_INTERNAL_RECORD"
            ),
            "confidence": bool(status_readback_verified),
            "dependencies": True,
            "alternatives": bool(rollback_ready),
            "judgement": bool("JUDGEMENT" in canonical_stages),
        },
        "body": {
            "capability": True,
            "permissions": bool(owner_scope_verified),
            "tools": True,
            "execution": bool(status_readback_verified),
            "verification": bool(
                status_readback_verified and content_unchanged
            ),
            "performance": True,
            "receipt": bool(audit_recorded),
        },
        "soul": {
            "purpose": bool(
                policy.get("external") is False
                and policy.get("authority_change") is False
            ),
            "human_benefit": bool(owner_scope_verified),
            "consent": bool(signed_approval_present),
            "integrity": bool(content_unchanged),
            "culture": True,
            "guardian_safety": bool("GUARDIAN" in canonical_stages),
            "human_authority": bool(
                authorization.get("human_authority_final") is True
                and "HUMAN_AUTHORITY" in canonical_stages
                and signed_approval_present
            ),
        },
    }


def execute(
    authorization: Mapping[str, object],
    *,
    identity_id: object,
    record_id: object,
    expected_status: object,
    target_status: object,
    expected_current_hash: object | None = None,
    expected_result_hash: object | None = None,
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

            current_hash_proof = _proof_hash(
                {
                    "workspace_id": workspace_id,
                    "title": title,
                    "body": body,
                    "status": current_status,
                }
            )
            if expected_current_hash is not None:
                expected_hash = str(expected_current_hash or "").strip().casefold()
                if (
                    len(expected_hash) != 64
                    or any(ch not in "0123456789abcdef" for ch in expected_hash)
                ):
                    raise ValueError("invalid_expected_current_hash")
                if current_hash_proof != expected_hash:
                    raise ExecutionBlocked("record_hash_mismatch")

            # Rollback restoration MUST be validated while holding the row lock
            # and before UPDATE/HRM/audit/commit. A post-commit mismatch cannot
            # safely be reported as a blocked, unperformed rollback.
            if expected_result_hash is not None:
                required_result = str(expected_result_hash or "").strip().casefold()
                if (len(required_result) != 64
                        or any(ch not in "0123456789abcdef"
                               for ch in required_result)):
                    raise ValueError("invalid_expected_result_hash")
                projected_result = _proof_hash({
                    "workspace_id": workspace_id,
                    "title": title,
                    "body": body,
                    "status": target,
                })
                if projected_result != required_result:
                    raise ExecutionBlocked("rollback_restoration_hash_mismatch")

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

            before_hash = current_hash_proof
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

            checks = _governance_checks(
                authorization,
                owner_scope_verified=True,
                status_readback_verified=status_verified,
                content_unchanged=content_unchanged,
                audit_recorded=True,
                rollback_ready=True,
            )
            outcome_receipt = governed_action_pipeline.record_action_outcome(
                authorization,
                idempotency_key=idempotency_key,
                action_performed=True,
                evidence_proven=True,
                checks=checks,
                connection=connection,
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
        "governance_checks": checks,
        "outcome_receipt": outcome_receipt,
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
        "rollback_hash_guard": True,
        "fresh_approval_required_for_rollback": True,
        "readback_required": True,
        "audit_required": True,
        "human_authority_final": True,
    }



def rollback(
    authorization: Mapping[str, object],
    *,
    identity_id: object,
    rollback_token: Mapping[str, object],
) -> dict[str, Any]:
    """Reverse one prior bounded execution after fresh governance approval."""

    if not isinstance(rollback_token, Mapping):
        raise TypeError("rollback_token_required")
    record_id = rollback_token.get("record_id")
    expected_status = rollback_token.get("expected_status")
    target_status = rollback_token.get("target_status")
    expected_current_hash = rollback_token.get("after_hash")
    expected_restored_hash = str(rollback_token.get("before_hash") or "").strip().casefold()
    if (
        len(expected_restored_hash) != 64
        or any(ch not in "0123456789abcdef" for ch in expected_restored_hash)
    ):
        raise ValueError("invalid_rollback_before_hash")

    result = execute(
        authorization,
        identity_id=identity_id,
        record_id=record_id,
        expected_status=expected_status,
        target_status=target_status,
        expected_current_hash=expected_current_hash,
        expected_result_hash=expected_restored_hash,
    )
    # Defensive consistency invariant; actual mismatch is blocked before write.
    if result["after_hash"] != expected_restored_hash:
        raise ExecutionBlocked("rollback_restoration_hash_mismatch")

    return {
        **result,
        "recovery_action": "ROLLBACK_INTERNAL_RECORD",
        "rollback_verified": True,
        "restored_hash": result["after_hash"],
        "original_before_hash": expected_restored_hash,
        "human_authority_final": True,
    }
