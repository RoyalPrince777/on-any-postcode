"""Production bridge from action-bound Founder approval to canonical Living Kernel.

This module adapts the existing PostgreSQL approval/audit store to the canonical
LivingKernel. It does not create a second kernel, approval authority, or builder.
Only already-registered GitHub Builder actions can execute, and every execution is
bound to one exact signed ActionPlan digest and one Human Authority receipt.
"""

from __future__ import annotations

import os
import uuid
from datetime import UTC
from typing import Any

from oap.contracts import (
    ActionPlan,
    ApprovalDecision,
    ApprovalReceipt,
    IdentityRecord,
    OutputState,
    Recommendation,
    SignalLevel,
    WarRoomReport,
    action_plan_digest,
)
from oap.hrm import ApprovalReceiptReplay
from oap.identity import IdentityEngine
from oap.kernel import BuilderRegistry, HumanApprovalAuthority, LivingKernel
from oap.smi.sovereign_controls import SovereignControlPlane
from oap.state_machine import ProcessingState

from . import approval_service, authority, postgres_db
from .founder_github_write import FounderGitHubWriteAdapter, register_github_builder_actions

_ALLOWED_ACTIONS = frozenset(
    {"github.branch.create", "github.file.write", "github.pr.create"}
)
_SOVEREIGN_CONTROLS = SovereignControlPlane()


class _ProductionKernelHRM:
    """Minimal HRM protocol adapter over the existing append-only audit chain."""

    def __init__(self, identity_id: str) -> None:
        self.identity_id = identity_id

    def record_approval(self, receipt: ApprovalReceipt) -> str:
        with postgres_db.connect() as connection:
            claimed = connection.execute(
                """UPDATE smi_approval_receipts
                   SET consumed_at=CURRENT_TIMESTAMP
                   WHERE receipt_id=%s AND request_id=%s AND identity_id=%s
                     AND decision='APPROVED' AND consumed_at IS NULL
                   RETURNING receipt_id""",
                (receipt.receipt_id, receipt.request_id, receipt.identity_id),
            ).fetchone()
            if not claimed:
                raise ApprovalReceiptReplay("Human Authority receipt replay blocked")
            approval_service._write_audit(
                connection,
                actor_id=self.identity_id,
                action="FOUNDER_TOOL_KERNEL_CLAIMED",
                target=receipt.request_id,
                reason="Living Kernel atomically consumed exact Founder action receipt.",
                correlation_id=receipt.request_id,
                metadata={
                    "request_id": receipt.request_id,
                    "receipt_id": receipt.receipt_id,
                    "action_digest": receipt.action_digest,
                    "authority_level": receipt.authority_level,
                    "execution_granted": True,
                    "sovereign_policy_fingerprint": (
                        _SOVEREIGN_CONTROLS.policy_fingerprint()
                    ),
                },
            )
            connection.commit()
        return receipt.receipt_id

    def record_kernel_result(self, result, receipt_id: str | None) -> str:
        with postgres_db.connect() as connection:
            approval_service._write_audit(
                connection,
                actor_id=self.identity_id,
                action=(
                    "FOUNDER_TOOL_KERNEL_EXECUTED"
                    if result.executed
                    else "FOUNDER_TOOL_KERNEL_BLOCKED"
                ),
                target=result.request_id,
                reason=result.reason,
                correlation_id=result.request_id,
                metadata={
                    "request_id": result.request_id,
                    "receipt_id": receipt_id,
                    "state": result.state,
                    "executed": bool(result.executed),
                    "processing_states": list(result.processing_states),
                    "sovereign_policy_fingerprint": (
                        _SOVEREIGN_CONTROLS.policy_fingerprint()
                    ),
                },
            )
            connection.commit()
        return "audit-recorded"


def _load_receipt(receipt_id: str, identity_id: str) -> ApprovalReceipt:
    with postgres_db.connect(readonly=True) as connection:
        authority.require_human_authority(connection, identity_id)
        row = connection.execute(
            """SELECT receipt_id,request_id,identity_id,authority_level,decision,
                      issued_at,expires_at,nonce,action_digest,signature,consumed_at
               FROM smi_approval_receipts
               WHERE receipt_id=%s AND identity_id=%s""",
            (receipt_id, identity_id),
        ).fetchone()
    if not row:
        raise PermissionError("Founder approval receipt was not found")
    if row[10] is not None:
        raise ApprovalReceiptReplay("Human Authority receipt replay blocked")
    return ApprovalReceipt(
        receipt_id=str(row[0]),
        request_id=str(row[1]),
        identity_id=str(row[2]),
        authority_level=int(row[3]),
        decision=ApprovalDecision(str(row[4])),
        issued_at=row[5].astimezone(UTC),
        expires_at=row[6].astimezone(UTC),
        nonce=str(row[7]),
        action_digest=str(row[8]),
        signature=str(row[9]),
    )


def _plan_from_payload(payload: dict[str, Any]) -> ActionPlan:
    try:
        request_id = str(uuid.UUID(str(payload.get("request_id"))))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError("Founder ActionPlan request_id must be a UUID") from exc
    action_type = str(payload.get("action_type") or "").strip()
    action_payload = payload.get("payload")
    if action_type not in _ALLOWED_ACTIONS or not isinstance(action_payload, dict):
        raise ValueError("Exact Founder ActionPlan is required")
    return ActionPlan(
        request_id=request_id,
        action_type=action_type,
        payload=action_payload,
        requires_human_approval=True,
    )


def execute_approved_action(
    *,
    identity_id: str,
    receipt_id: str,
    plan_payload: dict[str, Any],
) -> dict[str, object]:
    plan = _plan_from_payload(plan_payload)
    receipt = _load_receipt(str(receipt_id or "").strip(), identity_id)
    if receipt.request_id != plan.request_id:
        raise PermissionError("Approval receipt does not match ActionPlan request")
    if receipt.decision != ApprovalDecision.APPROVED:
        raise PermissionError("Founder action is not approved")

    digest_matches = action_plan_digest(plan) == receipt.action_digest
    if not digest_matches:
        raise PermissionError("Approval receipt does not match exact ActionPlan digest")

    approval_probe = approval_service.status()
    sovereign_review = _SOVEREIGN_CONTROLS.require_execution(
        action_type=plan.action_type,
        is_human_authority=True,
        authority_level=receipt.authority_level,
        signed_receipt=bool(receipt.signature),
        exact_action_digest=digest_matches,
        receipt_unconsumed=True,
        audit_ready=bool(approval_probe.get("ready")),
    )

    identity = IdentityEngine(
        (
            IdentityRecord(
                identity_id=identity_id,
                identity_type="human_authority",
                authority_level=0,
                status="ACTIVE",
                permissions=frozenset(
                    {HumanApprovalAuthority.APPROVAL_PERMISSION}
                ),
                roles=("Founder",),
            ),
        )
    )
    approval = HumanApprovalAuthority(identity, approval_service._signing_key())
    builders = BuilderRegistry()
    register_github_builder_actions(builders)
    kernel = LivingKernel(
        approval,
        builders,
        _ProductionKernelHRM(identity_id),
    )
    recommendation = Recommendation(
        request_id=plan.request_id,
        output_state=OutputState.REVIEW_REQUIRED,
        summary="Execute the exact Human-approved Founder GitHub ActionPlan.",
        rationale=(
            "Action is bound to a signed Human Authority receipt.",
            "SMI Sovereign Control Plane passed before Living Kernel execution.",
        ),
        signal_level=SignalLevel.YELLOW,
        advisor_ids=(),
        provider_ids=(),
        processing_states=(
            ProcessingState.RECEIVED.value,
            ProcessingState.IDENTITY_VERIFIED.value,
            ProcessingState.SMI_REVIEWED.value,
            ProcessingState.GUARDIAN_PASSED.value,
            ProcessingState.HUMAN_REVIEW_REQUIRED.value,
        ),
        human_review_required=True,
        war_room=WarRoomReport(
            triggered=False,
            scenarios=(),
            recommendation=(
                "Proceed only through Living Kernel after exact receipt and "
                "sovereign-control verification."
            ),
        ),
    )
    result = kernel.coordinate(recommendation, plan, receipt)
    return {
        "request_id": result.request_id,
        "executed": result.executed,
        "state": result.state,
        "reason": result.reason,
        "processing_states": list(result.processing_states),
        "audit_event_id": result.audit_event_id,
        "sovereign_controls": sovereign_review,
        "sovereign_policy_fingerprint": _SOVEREIGN_CONTROLS.policy_fingerprint(),
        "human_authority_final": True,
        "living_kernel": True,
    }


def status(*, branch: str | None = None) -> dict[str, object]:
    """Read configuration and scope only; never consume approval or call GitHub."""
    sovereign = _SOVEREIGN_CONTROLS.status()
    token_configured = bool(os.getenv("OAP_GITHUB_TOKEN", "").strip())
    try:
        approval_service._signing_key()
        signing_key_configured = True
    except approval_service.ApprovalUnavailable:
        signing_key_configured = False
    master_gate = (
        not sovereign["master_mode_requested"]
        or sovereign["master_full_sovereignty_ready"]
    )
    branch_allowed = None
    if branch is not None:
        try:
            FounderGitHubWriteAdapter._validated_branch(branch)
            branch_allowed = True
        except ValueError:
            branch_allowed = False
    configuration_ready = bool(
        token_configured and signing_key_configured
        and sovereign["execution_enabled"] and master_gate
    )
    return {
        "component": "Founder Living Kernel Execution Bridge",
        "ready": configuration_ready and branch_allowed is not False,
        "configuration_ready": configuration_ready,
        "token_configured": token_configured,
        "signing_key_configured": signing_key_configured,
        "branch_scope_allowed": branch_allowed,
        "branch_prefix": "oap-mind/",
        "native_worker_dispatch_connected": False,
        "native_engineering_execution_verified": False,
        "live_github_write_verified": False,
        "execution_granted": False,
        "evidence_class": "configuration_and_policy_only",
        "blockers": [
            name for name, blocked in (
                ("github_token_missing", not token_configured),
                ("approval_signing_key_missing_or_short", not signing_key_configured),
                ("emergency_halt_active", not sovereign["execution_enabled"]),
                ("master_sovereignty_gate_incomplete", not master_gate),
                ("branch_outside_existing_builder_scope", branch_allowed is False),
                ("native_engineering_dispatch_not_connected", True),
            ) if blocked
        ],
        "actions": sorted(_ALLOWED_ACTIONS),
        "requires_signed_receipt": True,
        "requires_exact_action_digest": True,
        "replay_protection": "smi_approval_receipts.consumed_at",
        "sovereign_controls": sovereign,
        "direct_main_write": False,
        "pr_merge": False,
        "render_deploy": False,
        "database_mutation": False,
        "human_authority_final": True,
    }
