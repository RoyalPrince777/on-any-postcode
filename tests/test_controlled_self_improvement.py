from __future__ import annotations

import json
import sqlite3
from dataclasses import replace

import pytest

from oap.audit import initialize_audit_schema
from oap.contracts import ApprovalDecision, BrainRequest, BuilderContext, IdentityRecord
from oap.hrm import initialize_brain_schema
from oap.kernel import BuilderRegistry, HumanApprovalAuthority, LivingKernel
from oap.smi.bootstrap import build_smi


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
        roles=("human_authority",),
    )
    brain = build_smi(connection, identities=(human,))
    authority = HumanApprovalAuthority(brain.identity, b"approval-key-" * 4)
    return connection, brain, authority


def _recommendation(brain, request_id: str):
    return brain.process(
        BrainRequest(
            request_id=request_id,
            identity_id="founder-1",
            content="Review a bounded controlled improvement candidate.",
            task_type="TECHNICAL",
            high_impact=True,
        )
    )


def _passing_candidate(brain, request_id: str):
    proposal = brain.evolution.propose(())
    candidate = brain.evolution.stage_candidate(
        proposal,
        request_id=request_id,
        baseline_version="smi-v1",
        candidate_version="smi-v1.1",
        changes={
            "scope": "routing_threshold",
            "from": 0.70,
            "to": 0.74,
        },
        change_summary="Raise one bounded routing confidence threshold.",
    )
    evaluation = brain.evolution.sandbox(
        candidate,
        checks={
            "compile": True,
            "regression_suite": True,
            "guardian_invariant": True,
            "human_authority_invariant": True,
        },
        baseline_score=0.92,
        candidate_score=0.95,
    )
    return candidate, evaluation


def test_controlled_improvement_is_visible_and_never_independent():
    _, brain, _ = _runtime()

    status = brain.status()
    evolution = status["controlled_self_improvement"]

    assert status["ready"] is True
    assert evolution["ready"] is True
    assert evolution["independent_apply"] is False
    assert evolution["sandbox_required"] is True
    assert evolution["human_approval_required"] is True
    assert evolution["reversibility_required"] is True


def test_failed_or_regressing_candidate_cannot_form_promotion_plan():
    _, brain, _ = _runtime()
    proposal = brain.evolution.propose(())
    candidate = brain.evolution.stage_candidate(
        proposal,
        request_id="evolution-failed",
        baseline_version="smi-v1",
        candidate_version="smi-v1.1",
        changes={"threshold": 0.74},
        change_summary="Candidate with failed evidence.",
    )
    evaluation = brain.evolution.sandbox(
        candidate,
        checks={"compile": True, "regression_suite": False},
        baseline_score=0.95,
        candidate_score=0.91,
    )

    assert evaluation.passed is False
    assert "regression_suite" in evaluation.regressions
    assert "candidate_score_below_baseline" in evaluation.regressions
    with pytest.raises(PermissionError, match="cannot be promoted"):
        brain.evolution.plan_promotion(evaluation)


def test_non_reversible_candidate_fails_closed():
    _, brain, _ = _runtime()
    proposal = brain.evolution.propose(())
    candidate = brain.evolution.stage_candidate(
        proposal,
        request_id="evolution-irreversible",
        baseline_version="smi-v1",
        candidate_version="smi-v2",
        changes={"mode": "irreversible"},
        change_summary="Intentionally non-reversible test candidate.",
        reversible=False,
    )
    evaluation = brain.evolution.sandbox(
        candidate,
        checks={"compile": True, "regression_suite": True},
        baseline_score=0.90,
        candidate_score=0.99,
    )

    assert evaluation.passed is False
    assert "candidate_not_reversible" in evaluation.regressions


def test_promotion_runs_only_through_signed_level_zero_kernel_path():
    connection, brain, authority = _runtime()
    recommendation = _recommendation(brain, "evolution-promote-1")
    candidate, evaluation = _passing_candidate(brain, recommendation.request_id)
    plan = brain.evolution.plan_promotion(evaluation)
    receipt = authority.issue(
        request_id=recommendation.request_id,
        identity_id="founder-1",
        decision=ApprovalDecision.APPROVED,
        plan=plan,
    )
    builders = BuilderRegistry()
    builders.register(
        brain.evolution.PROMOTE_ACTION,
        brain.evolution.apply_builder_promotion,
    )

    result = LivingKernel(authority, builders, brain.hrm).coordinate(
        recommendation,
        plan,
        receipt,
    )

    assert result.executed is True
    row = connection.execute(
        "SELECT actor_type, authority_level, metadata FROM audit_events "
        "WHERE action='EVOLUTION_PROMOTED' AND target=?",
        (candidate.candidate_id,),
    ).fetchone()
    assert row is not None
    assert row[0] == "human_authority"
    assert row[1] == 0
    metadata = json.loads(str(row[2]))
    assert metadata["approval_receipt_id"] == receipt.receipt_id
    assert metadata["baseline_version"] == "smi-v1"
    assert metadata["candidate_version"] == "smi-v1.1"
    assert metadata["independent_apply"] is False
    assert brain.evolution.status()["promotion_receipts"] == 1
    assert brain.hrm.status()["approval_receipts"] == 1


def test_direct_or_non_level_zero_promotion_is_blocked():
    _, brain, _ = _runtime()
    candidate, evaluation = _passing_candidate(brain, "evolution-direct-block")
    plan = brain.evolution.plan_promotion(evaluation)

    with pytest.raises(PermissionError, match="level-zero"):
        brain.evolution.apply_builder_promotion(
            plan.payload,
            BuilderContext(
                request_id=plan.request_id,
                receipt_id="not-authority",
                identity_id="member-1",
                authority_level=5,
                action_digest="not-signed",
            ),
        )
    with pytest.raises(PermissionError, match="cannot self-apply"):
        brain.evolution.apply(brain.evolution.propose(()))
    assert candidate.reversible is True


def test_approval_receipt_binds_exact_candidate_payload():
    _, brain, authority = _runtime()
    recommendation = _recommendation(brain, "evolution-bound-payload")
    _, evaluation = _passing_candidate(brain, recommendation.request_id)
    approved_plan = brain.evolution.plan_promotion(evaluation)
    receipt = authority.issue(
        request_id=recommendation.request_id,
        identity_id="founder-1",
        decision=ApprovalDecision.APPROVED,
        plan=approved_plan,
    )
    tampered_plan = replace(
        approved_plan,
        payload={**approved_plan.payload, "candidate_score": 1.0},
    )
    builders = BuilderRegistry()
    builders.register(
        brain.evolution.PROMOTE_ACTION,
        brain.evolution.apply_builder_promotion,
    )

    result = LivingKernel(authority, builders, brain.hrm).coordinate(
        recommendation,
        tampered_plan,
        receipt,
    )

    assert result.executed is False
    assert "invalid or expired" in result.reason
    assert brain.evolution.status()["promotion_receipts"] == 0


def test_rollback_requires_a_new_signed_human_approval_and_is_audited():
    connection, brain, authority = _runtime()
    recommendation = _recommendation(brain, "evolution-promote-rollback")
    candidate, evaluation = _passing_candidate(brain, recommendation.request_id)
    promotion_plan = brain.evolution.plan_promotion(evaluation)
    promotion_receipt = authority.issue(
        request_id=recommendation.request_id,
        identity_id="founder-1",
        decision=ApprovalDecision.APPROVED,
        plan=promotion_plan,
    )
    promotion_builders = BuilderRegistry()
    promotion_builders.register(
        brain.evolution.PROMOTE_ACTION,
        brain.evolution.apply_builder_promotion,
    )
    promoted = LivingKernel(authority, promotion_builders, brain.hrm).coordinate(
        recommendation,
        promotion_plan,
        promotion_receipt,
    )
    assert promoted.executed is True

    rollback_recommendation = _recommendation(brain, "evolution-rollback-1")
    rollback_plan = brain.evolution.plan_rollback(
        request_id=rollback_recommendation.request_id,
        candidate_id=candidate.candidate_id,
    )
    rollback_receipt = authority.issue(
        request_id=rollback_recommendation.request_id,
        identity_id="founder-1",
        decision=ApprovalDecision.APPROVED,
        plan=rollback_plan,
    )
    rollback_builders = BuilderRegistry()
    rollback_builders.register(
        brain.evolution.ROLLBACK_ACTION,
        brain.evolution.apply_builder_rollback,
    )
    rolled_back = LivingKernel(authority, rollback_builders, brain.hrm).coordinate(
        rollback_recommendation,
        rollback_plan,
        rollback_receipt,
    )

    assert rolled_back.executed is True
    row = connection.execute(
        "SELECT authority_level, metadata FROM audit_events "
        "WHERE action='EVOLUTION_ROLLED_BACK' AND target=?",
        (candidate.candidate_id,),
    ).fetchone()
    assert row is not None
    assert row[0] == 0
    metadata = json.loads(str(row[1]))
    assert metadata["approval_receipt_id"] == rollback_receipt.receipt_id
    assert metadata["restored_version"] == "smi-v1"
    assert metadata["replaced_version"] == "smi-v1.1"
    assert brain.evolution.status()["rollback_receipts"] == 1
    assert brain.hrm.status()["approval_receipts"] == 2

    with pytest.raises(PermissionError, match="already rolled back"):
        brain.evolution.plan_rollback(
            request_id="evolution-rollback-repeat",
            candidate_id=candidate.candidate_id,
        )
