"""Controlled learning proposals with sandbox, approval and rollback gates."""

from __future__ import annotations

import hashlib
import json
import math
import sqlite3
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from uuid import uuid4

from oap.audit import append_event, audit_schema_ready
from oap.contracts import (
    ActionPlan,
    BuilderContext,
    EvolutionProposal,
    KernelResult,
    utc_now,
)


@dataclass(frozen=True, slots=True)
class EvolutionCandidate:
    """A hashed, reversible candidate; it is not an applied system change."""

    candidate_id: str
    proposal_id: str
    request_id: str
    baseline_version: str
    candidate_version: str
    change_digest: str
    change_summary: str
    reversible: bool
    staged_at: object


@dataclass(frozen=True, slots=True)
class EvolutionEvaluation:
    """Evidence returned from an isolated candidate evaluation."""

    candidate: EvolutionCandidate
    checks: tuple[tuple[str, bool], ...]
    baseline_score: float
    candidate_score: float
    regressions: tuple[str, ...]
    passed: bool
    evaluated_at: object


class EvolutionEngine:
    """Prepare bounded improvements; never approve or self-apply them."""

    PROMOTE_ACTION = "promote_evolution_candidate"
    ROLLBACK_ACTION = "rollback_evolution_candidate"

    def __init__(self, connection: sqlite3.Connection | None = None) -> None:
        self.connection = connection

    def propose(self, outcomes: Iterable[KernelResult]) -> EvolutionProposal:
        records = tuple(outcomes)
        blocked = sum(not outcome.executed for outcome in records)
        evidence = (
            f"Reviewed outcomes: {len(records)}",
            f"Blocked outcomes: {blocked}",
        )
        return EvolutionProposal(
            proposal_id=str(uuid4()),
            title="Review SMI outcome patterns",
            description=(
                "Human Authority may review the evidence and approve a bounded "
                "refinement; no code, rule or permission changes automatically."
            ),
            evidence=evidence,
            requires_human_approval=True,
        )

    def stage_candidate(
        self,
        proposal: EvolutionProposal,
        *,
        request_id: str,
        baseline_version: str,
        candidate_version: str,
        changes: Mapping[str, object],
        change_summary: str,
        reversible: bool = True,
    ) -> EvolutionCandidate:
        """Hash a candidate without applying it to the running organism."""

        if not proposal.requires_human_approval:
            raise PermissionError("Evolution candidate must preserve Human Authority")
        request = self._text(request_id, "request_id")
        baseline = self._text(baseline_version, "baseline_version")
        candidate = self._text(candidate_version, "candidate_version")
        summary = self._text(change_summary, "change_summary")
        if baseline == candidate:
            raise ValueError("Candidate version must differ from baseline version")
        if not isinstance(changes, Mapping) or not changes:
            raise ValueError("Candidate changes must be a non-empty mapping")
        if any(not isinstance(key, str) or not key.strip() for key in changes):
            raise ValueError("Candidate change keys must be non-empty text")
        try:
            canonical = json.dumps(
                dict(changes),
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
                allow_nan=False,
            )
        except (TypeError, ValueError) as exc:
            raise ValueError("Candidate changes must be valid JSON") from exc
        return EvolutionCandidate(
            candidate_id=str(uuid4()),
            proposal_id=proposal.proposal_id,
            request_id=request,
            baseline_version=baseline,
            candidate_version=candidate,
            change_digest=hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
            change_summary=summary[:500],
            reversible=bool(reversible),
            staged_at=utc_now(),
        )

    def sandbox(
        self,
        candidate: EvolutionCandidate,
        *,
        checks: Mapping[str, bool],
        baseline_score: float,
        candidate_score: float,
    ) -> EvolutionEvaluation:
        """Evaluate supplied isolated-check evidence and fail closed on regression."""

        if not isinstance(checks, Mapping) or not checks:
            raise ValueError("Sandbox checks must be a non-empty mapping")
        normalized: list[tuple[str, bool]] = []
        for name, passed in checks.items():
            if not isinstance(name, str) or not name.strip() or type(passed) is not bool:
                raise ValueError("Sandbox checks must map text names to booleans")
            normalized.append((name.strip(), passed))
        baseline = self._score(baseline_score, "baseline_score")
        score = self._score(candidate_score, "candidate_score")
        ordered_checks = tuple(sorted(normalized))
        regressions = [name for name, passed in ordered_checks if not passed]
        if score < baseline:
            regressions.append("candidate_score_below_baseline")
        if not candidate.reversible:
            regressions.append("candidate_not_reversible")
        return EvolutionEvaluation(
            candidate=candidate,
            checks=ordered_checks,
            baseline_score=baseline,
            candidate_score=score,
            regressions=tuple(regressions),
            passed=not regressions,
            evaluated_at=utc_now(),
        )

    def plan_promotion(self, evaluation: EvolutionEvaluation) -> ActionPlan:
        """Bind one passing candidate to an exact Human-approved Builder plan."""

        if not evaluation.passed:
            raise PermissionError("Regressing or failed candidate cannot be promoted")
        candidate = evaluation.candidate
        return ActionPlan(
            request_id=candidate.request_id,
            action_type=self.PROMOTE_ACTION,
            payload={
                "proposal_id": candidate.proposal_id,
                "candidate_id": candidate.candidate_id,
                "baseline_version": candidate.baseline_version,
                "candidate_version": candidate.candidate_version,
                "change_digest": candidate.change_digest,
                "change_summary": candidate.change_summary,
                "reversible": candidate.reversible,
                "sandbox_passed": evaluation.passed,
                "checks": dict(evaluation.checks),
                "baseline_score": evaluation.baseline_score,
                "candidate_score": evaluation.candidate_score,
            },
            requires_human_approval=True,
        )

    def apply_builder_promotion(
        self,
        payload: dict[str, object],
        context: BuilderContext,
    ) -> None:
        """Record promotion only after Living Kernel supplies level-zero authority."""

        self._require_level_zero(context)
        self._require_audit()
        candidate_id = self._text(payload.get("candidate_id"), "candidate_id")
        proposal_id = self._text(payload.get("proposal_id"), "proposal_id")
        baseline = self._text(payload.get("baseline_version"), "baseline_version")
        candidate = self._text(payload.get("candidate_version"), "candidate_version")
        digest = self._digest(payload.get("change_digest"))
        if payload.get("sandbox_passed") is not True:
            raise PermissionError("Promotion requires a passing sandbox result")
        if payload.get("reversible") is not True:
            raise PermissionError("Promotion requires a reversible candidate")
        checks = payload.get("checks")
        if not isinstance(checks, dict) or not checks or not all(
            isinstance(name, str) and type(value) is bool and value
            for name, value in checks.items()
        ):
            raise PermissionError("Promotion requires all recorded checks to pass")
        baseline_score = self._score(payload.get("baseline_score"), "baseline_score")
        candidate_score = self._score(payload.get("candidate_score"), "candidate_score")
        if candidate_score < baseline_score:
            raise PermissionError("Promotion cannot regress below the baseline")
        if self._event_exists("EVOLUTION_PROMOTED", candidate_id):
            raise PermissionError("Evolution candidate is already promoted")
        append_event(
            self.connection,
            actor=context.identity_id,
            actor_type="human_authority",
            authority_level=context.authority_level,
            action="EVOLUTION_PROMOTED",
            target=candidate_id,
            reason="Human-approved controlled improvement promotion",
            metadata={
                "proposal_id": proposal_id,
                "approval_receipt_id": context.receipt_id,
                "baseline_version": baseline,
                "candidate_version": candidate,
                "change_digest": digest,
                "change_summary": str(payload.get("change_summary", ""))[:500],
                "baseline_score": baseline_score,
                "candidate_score": candidate_score,
                "checks": checks,
                "reversible": True,
                "independent_apply": False,
            },
            correlation_id=context.request_id,
        )

    def plan_rollback(self, *, request_id: str, candidate_id: str) -> ActionPlan:
        """Prepare a separately approved rollback for one promoted candidate."""

        self._require_audit()
        candidate = self._text(candidate_id, "candidate_id")
        if self._event_exists("EVOLUTION_ROLLED_BACK", candidate):
            raise PermissionError("Evolution candidate is already rolled back")
        row = self.connection.execute(
            "SELECT curr_hash, metadata FROM audit_events "
            "WHERE action = 'EVOLUTION_PROMOTED' AND target = ? "
            "ORDER BY event_seq DESC LIMIT 1",
            (candidate,),
        ).fetchone()
        if row is None:
            raise PermissionError("Only a promoted candidate can be rolled back")
        metadata = json.loads(str(row[1]))
        return ActionPlan(
            request_id=self._text(request_id, "request_id"),
            action_type=self.ROLLBACK_ACTION,
            payload={
                "candidate_id": candidate,
                "promotion_hash": str(row[0]),
                "restore_version": self._text(
                    metadata.get("baseline_version"), "baseline_version"
                ),
                "current_version": self._text(
                    metadata.get("candidate_version"), "candidate_version"
                ),
            },
            requires_human_approval=True,
        )

    def apply_builder_rollback(
        self,
        payload: dict[str, object],
        context: BuilderContext,
    ) -> None:
        """Record a verified rollback through the same Human-approved Kernel path."""

        self._require_level_zero(context)
        self._require_audit()
        candidate_id = self._text(payload.get("candidate_id"), "candidate_id")
        promotion_hash = self._text(payload.get("promotion_hash"), "promotion_hash")
        restore_version = self._text(payload.get("restore_version"), "restore_version")
        current_version = self._text(payload.get("current_version"), "current_version")
        if self._event_exists("EVOLUTION_ROLLED_BACK", candidate_id):
            raise PermissionError("Evolution candidate is already rolled back")
        row = self.connection.execute(
            "SELECT curr_hash, metadata FROM audit_events "
            "WHERE action = 'EVOLUTION_PROMOTED' AND target = ? "
            "ORDER BY event_seq DESC LIMIT 1",
            (candidate_id,),
        ).fetchone()
        if row is None or str(row[0]) != promotion_hash:
            raise PermissionError("Rollback does not match the recorded promotion")
        metadata = json.loads(str(row[1]))
        if (
            metadata.get("baseline_version") != restore_version
            or metadata.get("candidate_version") != current_version
        ):
            raise PermissionError("Rollback versions do not match the promotion receipt")
        append_event(
            self.connection,
            actor=context.identity_id,
            actor_type="human_authority",
            authority_level=context.authority_level,
            action="EVOLUTION_ROLLED_BACK",
            target=candidate_id,
            reason="Human-approved controlled improvement rollback",
            metadata={
                "approval_receipt_id": context.receipt_id,
                "promotion_hash": promotion_hash,
                "restored_version": restore_version,
                "replaced_version": current_version,
                "independent_apply": False,
            },
            correlation_id=context.request_id,
        )

    def apply(self, proposal: EvolutionProposal) -> None:
        del proposal
        raise PermissionError("Evolution proposals cannot self-apply")

    def status(self) -> dict[str, object]:
        ready = self.connection is not None and audit_schema_ready(self.connection)
        promotions = 0
        rollbacks = 0
        if ready:
            promotions = int(
                self.connection.execute(
                    "SELECT COUNT(*) FROM audit_events WHERE action = 'EVOLUTION_PROMOTED'"
                ).fetchone()[0]
            )
            rollbacks = int(
                self.connection.execute(
                    "SELECT COUNT(*) FROM audit_events "
                    "WHERE action = 'EVOLUTION_ROLLED_BACK'"
                ).fetchone()[0]
            )
        return {
            "component": "Controlled Self-Improvement",
            "ready": ready,
            "mode": "proposal_sandbox_human_approval",
            "independent_apply": False,
            "sandbox_required": True,
            "baseline_comparison_required": True,
            "human_approval_required": True,
            "reversibility_required": True,
            "promotion_receipts": promotions,
            "rollback_receipts": rollbacks,
        }

    def _require_audit(self) -> None:
        if self.connection is None or not audit_schema_ready(self.connection):
            raise RuntimeError("Evolution audit chain is not initialized")

    def _event_exists(self, action: str, target: str) -> bool:
        return (
            self.connection.execute(
                "SELECT 1 FROM audit_events WHERE action = ? AND target = ? LIMIT 1",
                (action, target),
            ).fetchone()
            is not None
        )

    @staticmethod
    def _require_level_zero(context: BuilderContext) -> None:
        if context.authority_level != 0:
            raise PermissionError("Only level-zero Human Authority may promote evolution")

    @staticmethod
    def _text(value: object, field: str) -> str:
        text = str(value or "").strip()
        if not text:
            raise ValueError(f"{field} is required")
        return text

    @staticmethod
    def _score(value: object, field: str) -> float:
        try:
            score = float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{field} must be numeric") from exc
        if not math.isfinite(score) or not 0 <= score <= 1:
            raise ValueError(f"{field} must be between 0 and 1")
        return score

    @staticmethod
    def _digest(value: object) -> str:
        digest = str(value or "").strip().casefold()
        if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
            raise ValueError("change_digest must be a SHA-256 hex digest")
        return digest
