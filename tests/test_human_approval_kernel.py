from __future__ import annotations

import sqlite3
from dataclasses import replace

import pytest

from oap.audit import initialize_audit_schema
from oap.contracts import (
    ApprovalDecision,
    BrainRequest,
    IdentityRecord,
    OutputState,
)
from oap.hrm import initialize_brain_schema
from oap.kernel import BuilderRegistry, HumanApprovalAuthority, LivingKernel
from oap.smi.action_engine import ActionEngine
from oap.smi.bootstrap import build_smi
from oap.smi.evolution_engine import EvolutionEngine
from oap.state_machine import (
    InvalidStateTransition,
    ProcessingState,
    RequestStateMachine,
)
from oap.world import WorldEngine


def _runtime():
    connection = sqlite3.connect(":memory:")
    initialize_audit_schema(connection)
    initialize_brain_schema(connection)
    human = IdentityRecord(
        identity_id="founder-1",
        identity_type="human_authority",
        authority_level=0,
        permissions=frozenset(
            {"REQUEST_RECOMMENDATION", "APPROVE_RECOMMENDATION"}
        ),
    )
    brain = build_smi(connection, identities=(human,))
    authority = HumanApprovalAuthority(brain.identity, b"approval-key-" * 4)
    return connection, brain, authority


def _recommendation(brain, request_id="kernel-request-1"):
    return brain.process(
        BrainRequest(
            request_id=request_id,
            identity_id="founder-1",
            content="Prepare a bounded local status record.",
        )
    )


def test_signed_human_approval_is_required_for_kernel_execution():
    _, brain, authority = _runtime()
    recommendation = _recommendation(brain)
    plan = ActionEngine().prepare(recommendation, action_type="record_status")
    receipt = authority.issue(
        request_id=recommendation.request_id,
        identity_id="founder-1",
        decision=ApprovalDecision.APPROVED,
        plan=plan,
    )
    seen = []
    builder = BuilderRegistry()
    builder.register(
        "record_status",
        lambda payload, context: seen.append((payload, context.receipt_id)),
    )

    result = LivingKernel(authority, builder, brain.hrm).coordinate(
        recommendation,
        plan,
        receipt,
    )

    assert result.executed is True
    assert result.state == "KERNEL_EXECUTED"
    assert result.processing_states[-3:] == (
        "HUMAN_APPROVED",
        "KERNEL_EXECUTED",
        "HRM_RECORDED",
    )
    assert seen == [({}, receipt.receipt_id)]
    assert brain.hrm.status()["kernel_outcomes"] == 1


def test_tampered_or_rejected_receipt_blocks_execution():
    _, brain, authority = _runtime()
    recommendation = _recommendation(brain, "kernel-request-2")
    plan = ActionEngine().prepare(recommendation, action_type="record_status")
    builder = BuilderRegistry()
    builder.register("record_status", lambda payload, context: None)
    valid = authority.issue(
        request_id=recommendation.request_id,
        identity_id="founder-1",
        decision=ApprovalDecision.APPROVED,
        plan=plan,
    )
    tampered = replace(valid, signature="0" * 64)

    invalid_result = LivingKernel(authority, builder, brain.hrm).coordinate(
        recommendation,
        plan,
        tampered,
    )

    next_recommendation = _recommendation(brain, "kernel-request-3")
    next_plan = ActionEngine().prepare(
        next_recommendation,
        action_type="record_status",
    )
    rejected = authority.issue(
        request_id=next_recommendation.request_id,
        identity_id="founder-1",
        decision=ApprovalDecision.REJECTED,
        plan=next_plan,
    )
    rejected_result = LivingKernel(authority, builder, brain.hrm).coordinate(
        next_recommendation,
        next_plan,
        rejected,
    )

    assert invalid_result.executed is False
    assert "invalid or expired" in invalid_result.reason
    assert rejected_result.executed is False
    assert "rejected" in rejected_result.reason
    assert "HUMAN_REJECTED" in rejected_result.processing_states


def test_approval_receipt_is_single_use_and_cannot_repeat_builder_action():
    _, brain, authority = _runtime()
    recommendation = _recommendation(brain, "kernel-request-single-use")
    plan = ActionEngine().prepare(recommendation, action_type="record_status")
    receipt = authority.issue(
        request_id=recommendation.request_id,
        identity_id="founder-1",
        decision=ApprovalDecision.APPROVED,
        plan=plan,
    )
    seen = []
    builder = BuilderRegistry()
    builder.register(
        "record_status",
        lambda payload, context: seen.append((payload, context.receipt_id)),
    )
    kernel = LivingKernel(authority, builder, brain.hrm)

    first = kernel.coordinate(recommendation, plan, receipt)
    replay = kernel.coordinate(recommendation, plan, receipt)

    assert first.executed is True
    assert replay.executed is False
    assert "already consumed" in replay.reason
    assert seen == [({}, receipt.receipt_id)]
    assert brain.hrm.status()["approval_receipts"] == 1


def test_approval_receipt_is_bound_to_exact_builder_plan():
    _, brain, authority = _runtime()
    recommendation = _recommendation(brain, "kernel-request-bound-plan")
    approved_plan = ActionEngine().prepare(
        recommendation,
        action_type="record_status",
        payload={"status": "reviewed"},
    )
    changed_plan = replace(approved_plan, payload={"status": "published"})
    receipt = authority.issue(
        request_id=recommendation.request_id,
        identity_id="founder-1",
        decision=ApprovalDecision.APPROVED,
        plan=approved_plan,
    )
    seen = []
    builder = BuilderRegistry()
    builder.register(
        "record_status",
        lambda payload, context: seen.append((payload, context.receipt_id)),
    )

    result = LivingKernel(authority, builder, brain.hrm).coordinate(
        recommendation,
        changed_plan,
        receipt,
    )

    assert result.executed is False
    assert "invalid or expired" in result.reason
    assert seen == []
    assert brain.hrm.status()["approval_receipts"] == 0


def test_malformed_recommendation_history_fails_closed():
    _, brain, authority = _runtime()
    recommendation = _recommendation(brain, "kernel-request-history")
    malformed = replace(
        recommendation,
        processing_states=("RECEIVED", "HUMAN_APPROVED"),
    )
    plan = ActionEngine().prepare(malformed, action_type="record_status")
    receipt = authority.issue(
        request_id=malformed.request_id,
        identity_id="founder-1",
        decision=ApprovalDecision.APPROVED,
        plan=plan,
    )
    seen = []
    builder = BuilderRegistry()
    builder.register(
        "record_status",
        lambda payload, context: seen.append((payload, context.receipt_id)),
    )

    result = LivingKernel(authority, builder, brain.hrm).coordinate(
        malformed,
        plan,
        receipt,
    )

    assert result.executed is False
    assert result.reason == "Recommendation processing history is invalid"
    assert result.processing_states == (
        "RECEIVED",
        "EXECUTION_BLOCKED",
        "HRM_RECORDED",
    )
    assert seen == []


def test_kernel_rejects_plan_that_removes_human_approval_gate():
    _, brain, authority = _runtime()
    recommendation = _recommendation(brain, "kernel-request-no-gate")
    safe_plan = ActionEngine().prepare(
        recommendation,
        action_type="record_status",
    )
    unsafe_plan = replace(
        safe_plan,
        requires_human_approval=False,
    )
    receipt = authority.issue(
        request_id=recommendation.request_id,
        identity_id="founder-1",
        decision=ApprovalDecision.APPROVED,
        plan=safe_plan,
    )

    result = LivingKernel(
        authority,
        BuilderRegistry(),
        brain.hrm,
    ).coordinate(recommendation, unsafe_plan, receipt)

    assert result.executed is False
    assert "remove the Human Authority gate" in result.reason


def test_approved_receipt_cannot_execute_unregistered_builder_action():
    _, brain, authority = _runtime()
    recommendation = _recommendation(brain, "kernel-request-4")
    plan = ActionEngine().prepare(recommendation, action_type="not_registered")
    receipt = authority.issue(
        request_id=recommendation.request_id,
        identity_id="founder-1",
        decision=ApprovalDecision.APPROVED,
        plan=plan,
    )

    result = LivingKernel(authority, BuilderRegistry(), brain.hrm).coordinate(
        recommendation,
        plan,
        receipt,
    )

    assert result.executed is False
    assert "No approved Builder handler" in result.reason


def test_action_engine_refuses_block_or_log_only_outputs():
    _, brain, _ = _runtime()
    blocked = brain.process(
        BrainRequest(
            request_id="kernel-request-blocked",
            identity_id="unknown",
            content="Execute immediately.",
        )
    )

    assert blocked.output_state == OutputState.BLOCK_REQUEST
    with pytest.raises(PermissionError, match="cannot form an action plan"):
        ActionEngine().prepare(blocked, action_type="anything")


def test_action_engine_rejects_unserializable_payload():
    _, brain, _ = _runtime()
    recommendation = _recommendation(brain, "kernel-request-invalid-payload")

    with pytest.raises(ValueError, match="valid JSON"):
        ActionEngine().prepare(
            recommendation,
            action_type="record_status",
            payload={"unsupported": object()},
        )


def test_world_state_update_runs_only_through_kernel_and_builder():
    connection, brain, authority = _runtime()
    recommendation = _recommendation(brain, "world-request-1")
    world = WorldEngine(connection)
    plan = world.plan_update(
        recommendation.request_id,
        "system.mode",
        {"value": "local-first"},
    )
    receipt = authority.issue(
        request_id=recommendation.request_id,
        identity_id="founder-1",
        decision=ApprovalDecision.APPROVED,
        plan=plan,
    )

    builder = BuilderRegistry()
    builder.register("update_world_state", world.apply_builder_update)

    result = LivingKernel(authority, builder, brain.hrm).coordinate(
        recommendation,
        plan,
        receipt,
    )

    assert result.executed is True
    assert world.snapshot() == {"system.mode": {"value": "local-first"}}
    assert connection.execute(
        "SELECT version FROM smi_world_state WHERE state_key = 'system.mode'"
    ).fetchone()[0] == 1
    assert not hasattr(world, "apply_approved_update")


def test_state_machine_rejects_approval_bypass():
    state = RequestStateMachine()

    with pytest.raises(InvalidStateTransition):
        state.advance(ProcessingState.HUMAN_APPROVED)
    assert state.history == ("RECEIVED",)


def test_evolution_can_propose_but_never_self_apply():
    proposal = EvolutionEngine().propose(())

    assert proposal.requires_human_approval is True
    with pytest.raises(PermissionError, match="cannot self-apply"):
        EvolutionEngine().apply(proposal)
