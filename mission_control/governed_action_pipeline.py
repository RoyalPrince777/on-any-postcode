"""Governed Signal -> Action boundary for OAP SMI.

This module joins the existing Signal/Guardian/Judgement/Human Authority records
without creating a second intelligence system. It never discovers or imports an
action dynamically. A caller must supply an explicitly registered action name,
and Human Authority approval must already exist as a valid signed receipt.

Execution and durable HRM persistence remain separate stages so an executor can
fail closed without pretending an external action succeeded.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Mapping

from . import approval_service, postgres_db
from .hrm_agent_lifecycle import BODY_7, MIND_7, SOUL_7
from .hrm_durable_receipt import build_receipt, persist_and_read_back


class ActionBlocked(RuntimeError):
    """A governed action cannot advance safely."""


CANONICAL_STAGES = (
    "SIGNAL",
    "AGENTS",
    "JUDGEMENT",
    "GUARDIAN",
    "HUMAN_AUTHORITY",
    "ACTION",
    "HRM_RECEIPT",
)


def _uuid(value: object, name: str) -> str:
    try:
        return str(uuid.UUID(str(value)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ActionBlocked(f"invalid_{name}") from exc


def _approval_row(request_id: str) -> tuple[Any, ...]:
    with postgres_db.connect(readonly=True) as connection:
        row = connection.execute(
            """SELECT receipt_id,request_id,identity_id,authority_level,
                      decision,issued_at,expires_at,action_digest,nonce,signature
               FROM smi_approval_receipts
               WHERE request_id=%s
               ORDER BY issued_at DESC LIMIT 1""",
            (request_id,),
        ).fetchone()
    if row is None:
        raise ActionBlocked("human_authority_approval_missing")
    return row


def _approval_valid(row: tuple[Any, ...], *, identity_id: str) -> bool:
    return bool(
        str(row[2]) == identity_id
        and int(row[3]) == 0
        and str(row[4]) == "APPROVED"
        and row[6] > datetime.now(timezone.utc)
        and approval_service._row_signature_valid(row)
    )


def authorize_action(
    *,
    signal_id: object,
    request_id: object,
    human_authority_identity_id: object,
    action_name: object,
    registered_actions: Mapping[str, object],
    guardian_passed: bool,
    judgement_consistent: bool,
    authority_transferred: bool = False,
) -> dict[str, object]:
    """Return an execution authorization only after every upstream gate passes.

    The returned authorization is evidence for a registered worker. This function
    does not itself execute the action and therefore cannot falsely claim success.
    """

    signal = str(signal_id or "").strip()
    action = str(action_name or "").strip()
    request = _uuid(request_id, "request_id")
    authority_identity = _uuid(human_authority_identity_id, "human_authority_identity_id")
    if not signal:
        raise ActionBlocked("signal_id_required")
    if not action or action not in registered_actions:
        raise ActionBlocked("registered_action_required")
    if guardian_passed is not True:
        raise ActionBlocked("guardian_gate_required")
    if judgement_consistent is not True:
        raise ActionBlocked("judgement_gate_required")
    if authority_transferred:
        raise ActionBlocked("authority_transfer_forbidden")

    row = _approval_row(request)
    if not _approval_valid(row, identity_id=authority_identity):
        raise ActionBlocked("human_authority_approval_invalid")

    return {
        "signal_id": signal,
        "request_id": request,
        "action_name": action,
        "approval_receipt_id": str(row[0]),
        "stages": CANONICAL_STAGES,
        "stage": "ACTION",
        "execution_authorized": True,
        "execution_performed": False,
        "authority_transferred": False,
        "human_authority_final": True,
    }


def record_action_outcome(
    authorization: Mapping[str, object],
    *,
    idempotency_key: object,
    action_performed: bool,
    evidence_proven: bool,
    checks: Mapping[str, Mapping[str, bool]],
) -> dict[str, object]:
    """Persist a durable HRM receipt only for a proven governed action outcome."""

    if authorization.get("execution_authorized") is not True:
        raise ActionBlocked("execution_authorization_required")
    if authorization.get("authority_transferred") is not False:
        raise ActionBlocked("authority_transfer_forbidden")
    if action_performed is not True:
        raise ActionBlocked("action_not_performed")
    if evidence_proven is not True:
        raise ActionBlocked("action_evidence_required")

    expected = {
        "mind": set(MIND_7),
        "body": set(BODY_7),
        "soul": set(SOUL_7),
    }
    if set(checks) != set(expected):
        raise ActionBlocked("canonical_governance_checks_required")
    for plane, required in expected.items():
        values = checks.get(plane)
        if not isinstance(values, Mapping) or set(values) != required:
            raise ActionBlocked(f"{plane}_canonical_checks_required")
        if not all(values[name] is True for name in required):
            raise ActionBlocked(f"{plane}_proof_incomplete")

    payload = {
        "governance": "7-7-7",
        "checks": {plane: dict(values) for plane, values in checks.items()},
        "evidence_proven": True,
        "authority_transferred": False,
        "human_authority_required": True,
        "human_authority_approved": True,
        "request_id": str(authorization["request_id"]),
        "action_name": str(authorization["action_name"]),
        "approval_receipt_id": str(authorization["approval_receipt_id"]),
        "execution_performed": True,
    }
    receipt = build_receipt(
        str(authorization["signal_id"]),
        payload,
        idempotency_key=str(idempotency_key or "").strip(),
    )
    result = persist_and_read_back(receipt)
    return {
        **result,
        "stage": "HRM_RECEIPT",
        "pipeline_complete": True,
        "human_authority_final": True,
    }
