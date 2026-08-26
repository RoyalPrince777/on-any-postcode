"""Governed Self-Improvement v2 for the single SMI brain.

The controller can autonomously detect explicit operational weaknesses, formulate
reversible candidate records and evaluate supplied sandbox evidence. A passing
candidate may produce a promotion *plan*, but only the existing signed
level-zero Human Authority + Living Kernel path can apply that plan.
"""
from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from typing import Any

from oap.contracts import ActionPlan

from .evolution_engine import EvolutionCandidate, EvolutionEngine, EvolutionEvaluation

AUTONOMY_MODE = "BOUNDED_AUTONOMOUS"


class SelfImprovementV2:
    """Automate review and candidate preparation without self-application."""

    def __init__(self, evolution: EvolutionEngine) -> None:
        self.evolution = evolution

    def status(self) -> dict[str, object]:
        base = self.evolution.status()
        return {
            "component": "SMI Self-Improvement v2",
            "ready": bool(base.get("ready")),
            "mode": AUTONOMY_MODE,
            "automatic_weakness_detection": True,
            "automatic_candidate_formulation": True,
            "automatic_sandbox_comparison": True,
            "automatic_promotion_plan_generation": True,
            "sandbox_required": True,
            "baseline_comparison_required": True,
            "reversibility_required": True,
            "human_approval_required": True,
            "living_kernel_required": True,
            "independent_approval": False,
            "independent_apply": False,
            "independent_rollback": False,
            "human_authority_final": True,
        }

    def detect_weaknesses(self, evidence: Mapping[str, object]) -> tuple[str, ...]:
        """Convert explicit health/coherence evidence into bounded weakness labels."""
        if not isinstance(evidence, Mapping):
            raise TypeError("improvement evidence must be a mapping")

        weaknesses: list[str] = []
        for item in evidence.get("degraded_components", ()) or ():
            text = str(item).strip()
            if text:
                weaknesses.append(f"degraded:{text[:120]}")
        for item in evidence.get("unknown_components", ()) or ():
            text = str(item).strip()
            if text:
                weaknesses.append(f"unknown:{text[:120]}")
        for item in evidence.get("coherence_conflicts", ()) or ():
            text = str(item).strip()
            if text:
                weaknesses.append(f"coherence:{text[:120]}")

        boolean_checks = (
            ("runtime_worker_fresh", "runtime_worker_not_fresh"),
            ("product_cores_ready", "product_cores_not_ready"),
            ("routing_production_ready", "routing_not_production_ready"),
            ("movement_ready", "movement_not_ready"),
        )
        for field, label in boolean_checks:
            if field in evidence and evidence.get(field) is not True:
                weaknesses.append(label)

        # Preserve order while deduplicating and cap autonomous scope.
        return tuple(dict.fromkeys(weaknesses))[:20]

    def formulate_candidate(
        self,
        *,
        request_id: str,
        baseline_version: str,
        evidence: Mapping[str, object],
    ) -> EvolutionCandidate | None:
        """Form a reversible candidate record; never apply or promote it."""
        weaknesses = self.detect_weaknesses(evidence)
        if not weaknesses:
            return None
        proposal = self.evolution.propose(())
        canonical = json.dumps(weaknesses, separators=(",", ":"), ensure_ascii=False)
        fingerprint = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:12]
        return self.evolution.stage_candidate(
            proposal,
            request_id=request_id,
            baseline_version=baseline_version,
            candidate_version=f"candidate-{fingerprint}",
            changes={
                "mode": "bounded_refinement",
                "review_targets": weaknesses,
                "authority_boundary": "human_final",
            },
            change_summary=(
                "Autonomous bounded refinement candidate for: "
                + ", ".join(weaknesses)
            )[:500],
            reversible=True,
        )

    def evaluate_candidate(
        self,
        candidate: EvolutionCandidate,
        *,
        checks: Mapping[str, bool],
        baseline_score: float,
        candidate_score: float,
    ) -> EvolutionEvaluation:
        """Compare isolated evidence using the existing fail-closed sandbox gate."""
        return self.evolution.sandbox(
            candidate,
            checks=checks,
            baseline_score=baseline_score,
            candidate_score=candidate_score,
        )

    def promotion_plan(self, evaluation: EvolutionEvaluation) -> ActionPlan:
        """Generate an approval-bound plan; this does not execute promotion."""
        return self.evolution.plan_promotion(evaluation)

    def review_cycle(
        self,
        *,
        request_id: str,
        baseline_version: str,
        evidence: Mapping[str, object],
        checks: Mapping[str, bool] | None = None,
        baseline_score: float | None = None,
        candidate_score: float | None = None,
    ) -> dict[str, Any]:
        """Run detect → formulate → optional sandbox → optional promotion-plan."""
        weaknesses = self.detect_weaknesses(evidence)
        candidate = self.formulate_candidate(
            request_id=request_id,
            baseline_version=baseline_version,
            evidence=evidence,
        )
        if candidate is None:
            return {
                "kind": "self_improvement_v2_cycle",
                "weaknesses": (),
                "candidate": None,
                "evaluation": None,
                "promotion_plan": None,
                "action": "maintain_current_configuration",
                "requires_human_approval": True,
                "independent_apply": False,
                "consequential_action": False,
            }

        candidate_view = {
            "candidate_id": candidate.candidate_id,
            "baseline_version": candidate.baseline_version,
            "candidate_version": candidate.candidate_version,
            "change_digest": candidate.change_digest,
            "change_summary": candidate.change_summary,
            "reversible": candidate.reversible,
        }
        if checks is None:
            return {
                "kind": "self_improvement_v2_cycle",
                "weaknesses": weaknesses,
                "candidate": candidate_view,
                "evaluation": None,
                "promotion_plan": None,
                "action": "sandbox_evidence_required",
                "requires_human_approval": True,
                "independent_apply": False,
                "consequential_action": False,
            }
        if baseline_score is None or candidate_score is None:
            raise ValueError("sandbox scores are required when checks are supplied")

        evaluation = self.evaluate_candidate(
            candidate,
            checks=checks,
            baseline_score=baseline_score,
            candidate_score=candidate_score,
        )
        evaluation_view = {
            "passed": evaluation.passed,
            "checks": dict(evaluation.checks),
            "baseline_score": evaluation.baseline_score,
            "candidate_score": evaluation.candidate_score,
            "regressions": evaluation.regressions,
        }
        plan_view: dict[str, object] | None = None
        action = "candidate_rejected"
        if evaluation.passed:
            plan = self.promotion_plan(evaluation)
            plan_view = {
                "request_id": plan.request_id,
                "action_type": plan.action_type,
                "requires_human_approval": plan.requires_human_approval,
                "candidate_id": candidate.candidate_id,
            }
            action = "human_approval_required"

        return {
            "kind": "self_improvement_v2_cycle",
            "weaknesses": weaknesses,
            "candidate": candidate_view,
            "evaluation": evaluation_view,
            "promotion_plan": plan_view,
            "action": action,
            "requires_human_approval": True,
            "independent_apply": False,
            "consequential_action": False,
        }
