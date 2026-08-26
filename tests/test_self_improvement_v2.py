from __future__ import annotations

import sqlite3

import pytest

from oap.audit import initialize_audit_schema
from oap.hrm import initialize_brain_schema
from oap.smi.evolution_engine import EvolutionEngine
from oap.smi.self_improvement_v2 import SelfImprovementV2


def _controller() -> SelfImprovementV2:
    connection = sqlite3.connect(":memory:")
    initialize_audit_schema(connection)
    initialize_brain_schema(connection)
    return SelfImprovementV2(EvolutionEngine(connection))


def test_v2_policy_automates_preparation_but_never_authority():
    state = _controller().status()

    assert state["ready"] is True
    assert state["mode"] == "BOUNDED_AUTONOMOUS"
    assert state["automatic_weakness_detection"] is True
    assert state["automatic_candidate_formulation"] is True
    assert state["automatic_sandbox_comparison"] is True
    assert state["automatic_promotion_plan_generation"] is True
    assert state["sandbox_required"] is True
    assert state["reversibility_required"] is True
    assert state["human_approval_required"] is True
    assert state["living_kernel_required"] is True
    assert state["independent_approval"] is False
    assert state["independent_apply"] is False
    assert state["independent_rollback"] is False
    assert state["human_authority_final"] is True


def test_v2_detects_explicit_cross_organ_weaknesses():
    controller = _controller()

    weaknesses = controller.detect_weaknesses(
        {
            "degraded_components": ("routing",),
            "unknown_components": ("weather",),
            "coherence_conflicts": ("provider mismatch",),
            "runtime_worker_fresh": False,
            "product_cores_ready": True,
            "routing_production_ready": False,
            "movement_ready": True,
        }
    )

    assert "degraded:routing" in weaknesses
    assert "unknown:weather" in weaknesses
    assert "coherence:provider mismatch" in weaknesses
    assert "runtime_worker_not_fresh" in weaknesses
    assert "routing_not_production_ready" in weaknesses
    assert "product_cores_not_ready" not in weaknesses


def test_v2_autonomously_formulates_reversible_candidate_without_applying():
    controller = _controller()

    cycle = controller.review_cycle(
        request_id="autonomy-improvement-1",
        baseline_version="smi-v1",
        evidence={"runtime_worker_fresh": False},
    )

    assert cycle["candidate"] is not None
    assert cycle["candidate"]["reversible"] is True
    assert cycle["evaluation"] is None
    assert cycle["promotion_plan"] is None
    assert cycle["action"] == "sandbox_evidence_required"
    assert cycle["requires_human_approval"] is True
    assert cycle["independent_apply"] is False
    assert cycle["consequential_action"] is False


def test_v2_regression_fails_closed_and_produces_no_promotion_plan():
    controller = _controller()

    cycle = controller.review_cycle(
        request_id="autonomy-improvement-regression",
        baseline_version="smi-v1",
        evidence={"routing_production_ready": False},
        checks={
            "compile": True,
            "regression_suite": False,
            "guardian_invariant": True,
            "human_authority_invariant": True,
        },
        baseline_score=0.95,
        candidate_score=0.90,
    )

    assert cycle["evaluation"]["passed"] is False
    assert "regression_suite" in cycle["evaluation"]["regressions"]
    assert "candidate_score_below_baseline" in cycle["evaluation"]["regressions"]
    assert cycle["promotion_plan"] is None
    assert cycle["action"] == "candidate_rejected"
    assert cycle["consequential_action"] is False


def test_v2_passing_sandbox_only_generates_human_approval_plan():
    controller = _controller()

    cycle = controller.review_cycle(
        request_id="autonomy-improvement-pass",
        baseline_version="smi-v1",
        evidence={"routing_production_ready": False},
        checks={
            "compile": True,
            "regression_suite": True,
            "guardian_invariant": True,
            "human_authority_invariant": True,
            "rollback_proof": True,
        },
        baseline_score=0.92,
        candidate_score=0.96,
    )

    assert cycle["evaluation"]["passed"] is True
    assert cycle["promotion_plan"] is not None
    assert cycle["promotion_plan"]["requires_human_approval"] is True
    assert cycle["action"] == "human_approval_required"
    assert cycle["independent_apply"] is False
    assert cycle["consequential_action"] is False


def test_v2_healthy_evidence_makes_no_candidate():
    controller = _controller()

    cycle = controller.review_cycle(
        request_id="autonomy-improvement-clean",
        baseline_version="smi-v1",
        evidence={
            "runtime_worker_fresh": True,
            "product_cores_ready": True,
            "routing_production_ready": True,
            "movement_ready": True,
        },
    )

    assert cycle["weaknesses"] == ()
    assert cycle["candidate"] is None
    assert cycle["action"] == "maintain_current_configuration"


def test_v2_requires_scores_when_sandbox_checks_are_supplied():
    controller = _controller()

    with pytest.raises(ValueError, match="sandbox scores"):
        controller.review_cycle(
            request_id="autonomy-improvement-missing-score",
            baseline_version="smi-v1",
            evidence={"runtime_worker_fresh": False},
            checks={"compile": True},
        )
