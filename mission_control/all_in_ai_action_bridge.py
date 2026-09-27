"""Governed ALL IN A.I. mission -> SMI action authorization bridge.

This module is deliberately non-executing. It derives action readiness from
already durable evidence: the owner-scoped Mission Keeper receipt, a real SMI
Guardian/Judgement review, and the existing signed Human Authority approval
receipt. No new approval, memory or execution system is created here.
"""

from __future__ import annotations

import uuid
from collections.abc import Mapping
from typing import Any

from . import (
    all_in_ai_mission_store,
    governed_action_pipeline,
    internal_record_executor,
    postgres_db,
)


class ActionHandoffBlocked(RuntimeError):
    """The Mission Keeper handoff cannot advance safely."""


def _uuid(value: object, name: str) -> str:
    try:
        return str(uuid.UUID(str(value)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError(f"invalid_{name}") from exc


def _review_status(identity_id: str, request_id: str) -> dict[str, Any]:
    try:
        with postgres_db.connect(readonly=True) as connection:
            row = connection.execute(
                """SELECT
                       m.request_id,
                       m.output_state,
                       g.outcome,
                       j.sections_completed,
                       j.constitution_consistent,
                       j.human_decision
                   FROM smi_memory_records m
                   JOIN oap_guardian_reviews g
                     ON g.request_id=m.request_id
                    AND g.identity_id=m.identity_id
                   JOIN smi_judgement_reviews j
                     ON j.request_id=m.request_id
                    AND j.identity_id=m.identity_id
                   WHERE m.request_id=%s
                     AND m.identity_id=%s
                   LIMIT 1""",
                (request_id, identity_id),
            ).fetchone()
    except Exception as exc:
        raise ActionHandoffBlocked("review_store_unavailable") from exc

    if row is None:
        raise ActionHandoffBlocked("reviewed_request_not_found")

    guardian_outcome = str(row[2] or "")
    sections_completed = int(row[3] or 0)
    constitution_consistent = bool(row[4])
    human_decision = str(row[5]) if row[5] else None
    guardian_passed = guardian_outcome == "PASSED"
    judgement_consistent = bool(
        sections_completed == 5 and constitution_consistent
    )

    return {
        "request_id": str(row[0]),
        "output_state": str(row[1]),
        "guardian_outcome": guardian_outcome,
        "guardian_passed": guardian_passed,
        "judgement_sections_completed": sections_completed,
        "judgement_consistent": judgement_consistent,
        "human_decision": human_decision,
    }


def handoff_status(
    identity_id: object,
    mission_id: object,
    *,
    reviewed_request_id: object,
    action_name: object = "SYNC_INTERNAL_RECORD",
) -> dict[str, Any]:
    """Evaluate one mission handoff without performing the registered action."""

    identity = _uuid(identity_id, "identity_id")
    mission = _uuid(mission_id, "mission_id")
    request_id = _uuid(reviewed_request_id, "reviewed_request_id")
    action = str(action_name or "").strip()

    if action not in governed_action_pipeline.REGISTERED_ACTIONS:
        raise ValueError("registered_action_required")

    mission_receipt = all_in_ai_mission_store.read(identity, mission)
    if mission_receipt.get("state") == "stopped":
        raise ActionHandoffBlocked("mission_stopped")
    if not (
        mission_receipt.get("read_back_verified") is True
        and mission_receipt.get("audit_verified") is True
        and mission_receipt.get("hrm_verified") is True
    ):
        raise ActionHandoffBlocked("mission_receipt_unverified")

    review = _review_status(identity, request_id)
    base = {
        "component": "ALL IN A.I. Governed Action Handoff",
        "mission_id": mission,
        "reviewed_request_id": request_id,
        "action_name": action,
        "action_policy": dict(
            governed_action_pipeline.REGISTERED_ACTIONS[action]
        ),
        "mission_state": str(mission_receipt.get("state") or ""),
        "mission_receipt_verified": True,
        "review": review,
        "human_authority_required": True,
        "execution_performed": False,
        "authority_transferred": False,
        "human_authority_final": True,
    }

    if not review["guardian_passed"]:
        return {
            **base,
            "status": "BLOCKED",
            "reason": "guardian_gate_required",
            "execution_authorized": False,
        }
    if not review["judgement_consistent"]:
        return {
            **base,
            "status": "BLOCKED",
            "reason": "judgement_gate_required",
            "execution_authorized": False,
        }
    if review["human_decision"] != "APPROVED":
        return {
            **base,
            "status": "HUMAN_AUTHORITY_REQUIRED",
            "reason": (
                "human_authority_rejected"
                if review["human_decision"] == "REJECTED"
                else "human_authority_approval_required"
            ),
            "execution_authorized": False,
        }

    try:
        authorization = governed_action_pipeline.authorize_action(
            signal_id=f"all-in-ai:{mission}",
            request_id=request_id,
            human_authority_identity_id=identity,
            action_name=action,
            guardian_passed=True,
            judgement_consistent=True,
            authority_transferred=False,
        )
    except governed_action_pipeline.ActionBlocked as exc:
        return {
            **base,
            "status": "BLOCKED",
            "reason": str(exc),
            "execution_authorized": False,
        }

    return {
        **base,
        "status": "AUTHORIZED_NOT_EXECUTED",
        "reason": "all_governance_gates_passed",
        "authorization": authorization,
        "execution_authorized": True,
        "execution_performed": False,
    }


def status() -> dict[str, Any]:
    """Project the bounded action-handoff capability without claiming execution."""

    return {
        "component": "ALL IN A.I. Governed Action Handoff",
        "registered_actions": tuple(
            sorted(governed_action_pipeline.REGISTERED_ACTIONS)
        ),
        "mission_receipt_required": True,
        "guardian_required": True,
        "judgement_required": True,
        "signed_human_approval_required": True,
        "execution_authority_created": False,
        "execution_performed_by_bridge": False,
        "bounded_executor": internal_record_executor.status(),
        "authority_transferred": False,
        "human_authority_final": True,
    }


def execute_internal_record(
    identity_id: object,
    mission_id: object,
    *,
    reviewed_request_id: object,
    record_id: object,
    expected_status: object,
    target_status: object,
) -> dict[str, Any]:
    """Execute the one bounded registered internal action after fresh governance."""

    handoff = handoff_status(
        identity_id,
        mission_id,
        reviewed_request_id=reviewed_request_id,
        action_name="SYNC_INTERNAL_RECORD",
    )
    if handoff.get("status") != "AUTHORIZED_NOT_EXECUTED":
        raise ActionHandoffBlocked(str(handoff.get("reason") or "action_not_authorized"))
    authorization = handoff.get("authorization")
    if not isinstance(authorization, dict):
        raise ActionHandoffBlocked("authorization_receipt_missing")

    execution = internal_record_executor.execute(
        authorization,
        identity_id=identity_id,
        record_id=record_id,
        expected_status=expected_status,
        target_status=target_status,
    )
    return {
        "component": "ALL IN A.I. Governed Internal Execution",
        "mission_id": handoff["mission_id"],
        "reviewed_request_id": handoff["reviewed_request_id"],
        "handoff_status": handoff["status"],
        "execution": execution,
        "execution_authorized": True,
        "execution_performed": True,
        "outcome_receipt_verified": bool(
            execution.get("outcome_receipt", {}).get("write_verified")
            and execution.get("outcome_receipt", {}).get("read_back_verified")
        ),
        "authority_transferred": False,
        "human_authority_final": True,
    }



def rollback_internal_record(
    identity_id: object,
    mission_id: object,
    *,
    reviewed_request_id: object,
    rollback_token: Mapping[str, object],
) -> dict[str, Any]:
    """Reverse one bounded internal action after a fresh governed handoff."""

    handoff = handoff_status(
        identity_id,
        mission_id,
        reviewed_request_id=reviewed_request_id,
        action_name="SYNC_INTERNAL_RECORD",
    )
    if handoff.get("status") != "AUTHORIZED_NOT_EXECUTED":
        raise ActionHandoffBlocked(str(handoff.get("reason") or "rollback_not_authorized"))
    authorization = handoff.get("authorization")
    if not isinstance(authorization, dict):
        raise ActionHandoffBlocked("authorization_receipt_missing")

    recovery = internal_record_executor.rollback(
        authorization,
        identity_id=identity_id,
        rollback_token=rollback_token,
    )
    return {
        "component": "ALL IN A.I. Governed Internal Recovery",
        "mission_id": handoff["mission_id"],
        "reviewed_request_id": handoff["reviewed_request_id"],
        "handoff_status": handoff["status"],
        "recovery": recovery,
        "rollback_verified": bool(recovery.get("rollback_verified")),
        "outcome_receipt_verified": bool(
            recovery.get("outcome_receipt", {}).get("write_verified")
            and recovery.get("outcome_receipt", {}).get("read_back_verified")
        ),
        "authority_transferred": False,
        "human_authority_final": True,
    }
