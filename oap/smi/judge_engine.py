"""Governed judgement intelligence for Sovereign Megaverse Intelligence.

Judgement evaluates integrated reasoning and safety evidence, but it never
executes work or overrides the Human Authority boundary.  ``decide`` preserves
the established runtime contract while the richer review methods expose the
reasoning behind that bounded output state.
"""

from __future__ import annotations

from dataclasses import dataclass

from oap.contracts import (
    BrainRequest,
    IntegratedAnalysis,
    OutputState,
    SafetyDecision,
    SignalLevel,
)


_SIGNAL_WEIGHT = {
    SignalLevel.GREEN: 0,
    SignalLevel.WHITE: 0,
    SignalLevel.YELLOW: 1,
    SignalLevel.ORANGE: 2,
    SignalLevel.RED: 3,
}


@dataclass(frozen=True, slots=True)
class JudgementReport:
    """Evidence-backed judgement summary; never an execution authority."""

    output_state: OutputState
    quality_score: float
    confidence_score: float
    risk_score: int
    evidence_count: int
    blocking_findings: tuple[str, ...]
    review_reasons: tuple[str, ...]
    rationale: tuple[str, ...]
    human_review_required: bool

    @property
    def can_execute(self) -> bool:
        """Judgement is recommendation-only by constitutional design."""

        return False


class JudgeEngine:
    """Evaluate consequence, evidence, quality, risk and review requirements."""

    def evaluate_information(self, analysis: IntegratedAnalysis) -> float:
        """Score integrated information quality from confidence and findings."""

        confidence = max(0.0, min(1.0, float(analysis.confidence)))
        if not analysis.findings:
            return round(confidence * 0.5, 3)
        supported = sum(
            max(0.0, min(1.0, float(finding.confidence)))
            for finding in analysis.findings
        ) / len(analysis.findings)
        return round((confidence + supported) / 2, 3)

    def evaluate_reasoning(self, analysis: IntegratedAnalysis) -> dict[str, object]:
        """Check coherence of the integrated reasoning result."""

        summaries = tuple(
            finding.summary.strip()
            for finding in analysis.findings
            if finding.summary.strip()
        )
        organ_ids = tuple(finding.organ_id for finding in analysis.findings)
        duplicate_organs = tuple(
            organ_id for organ_id in sorted(set(organ_ids)) if organ_ids.count(organ_id) > 1
        )
        return {
            "summary_present": bool(analysis.summary.strip()),
            "finding_count": len(analysis.findings),
            "supported_findings": len(summaries),
            "duplicate_organs": duplicate_organs,
            "coherent": bool(analysis.summary.strip()) and not duplicate_organs,
        }

    def evaluate_evidence(self, analysis: IntegratedAnalysis) -> dict[str, object]:
        """Measure evidence coverage without inventing external evidence."""

        evidence_count = len(analysis.findings)
        high_confidence = sum(
            1 for finding in analysis.findings if finding.confidence >= 0.75
        )
        low_confidence = tuple(
            finding.organ_id
            for finding in analysis.findings
            if finding.confidence < 0.5
        )
        return {
            "evidence_count": evidence_count,
            "high_confidence_count": high_confidence,
            "low_confidence_organs": low_confidence,
            "coverage": 0.0 if evidence_count == 0 else round(high_confidence / evidence_count, 3),
        }

    def assess_risk(
        self,
        request: BrainRequest,
        analysis: IntegratedAnalysis,
        safety: SafetyDecision,
    ) -> dict[str, object]:
        """Calculate bounded risk from explicit runtime signals only."""

        blocking = tuple(
            f"{finding.system}:{finding.code}"
            for finding in safety.findings
            if finding.blocks
        )
        highest_signal = max(
            _SIGNAL_WEIGHT[safety.signal_level],
            _SIGNAL_WEIGHT[analysis.signal_level],
        )
        risk_score = highest_signal
        if request.high_impact:
            risk_score += 1
        if safety.human_review_required:
            risk_score += 1
        if blocking or not safety.passed:
            risk_score = max(risk_score, 3)
        return {
            "score": risk_score,
            "blocking_findings": blocking,
            "high_impact": request.high_impact,
            "human_review_required": safety.human_review_required,
            "safety_passed": safety.passed,
        }

    def review_rules(
        self,
        request: BrainRequest,
        analysis: IntegratedAnalysis,
        safety: SafetyDecision,
    ) -> tuple[str, ...]:
        """Return concrete reasons requiring block or Human Authority review."""

        reasons: list[str] = []
        if not safety.passed:
            reasons.append("safety_not_passed")
        if safety.signal_level in {SignalLevel.ORANGE, SignalLevel.RED}:
            reasons.append(f"safety_signal_{safety.signal_level.value.lower()}")
        if analysis.signal_level in {SignalLevel.ORANGE, SignalLevel.RED}:
            reasons.append(f"analysis_signal_{analysis.signal_level.value.lower()}")
        if request.high_impact:
            reasons.append("high_impact_request")
        if safety.human_review_required:
            reasons.append("safety_requires_human_review")
        if analysis.signal_level == SignalLevel.YELLOW:
            reasons.append("analysis_requires_review")
        if not analysis.summary.strip():
            reasons.append("analysis_summary_missing")
        if not analysis.findings:
            reasons.append("analysis_evidence_missing")
        return tuple(dict.fromkeys(reasons))

    def decide(
        self,
        request: BrainRequest,
        analysis: IntegratedAnalysis,
        safety: SafetyDecision,
    ) -> OutputState:
        """Return the only output state SMI may produce independently."""

        if not safety.passed or safety.signal_level in {
            SignalLevel.ORANGE,
            SignalLevel.RED,
        }:
            return OutputState.BLOCK_REQUEST
        if analysis.signal_level in {SignalLevel.ORANGE, SignalLevel.RED}:
            return OutputState.BLOCK_REQUEST
        if request.task_type == OutputState.SYSTEM_LOG_ONLY.value:
            return OutputState.SYSTEM_LOG_ONLY
        if (
            request.high_impact
            or safety.human_review_required
            or analysis.signal_level == SignalLevel.YELLOW
            or not analysis.summary.strip()
            or not analysis.findings
        ):
            return OutputState.REVIEW_REQUIRED
        return OutputState.RECOMMENDATION_READY

    def review(
        self,
        request: BrainRequest,
        analysis: IntegratedAnalysis,
        safety: SafetyDecision,
    ) -> JudgementReport:
        """Run the complete judgement review while remaining fail-closed."""

        quality = self.evaluate_information(analysis)
        reasoning = self.evaluate_reasoning(analysis)
        evidence = self.evaluate_evidence(analysis)
        risk = self.assess_risk(request, analysis, safety)
        reasons = self.review_rules(request, analysis, safety)
        output_state = self.decide(request, analysis, safety)

        rationale: list[str] = [
            f"quality_score={quality:.3f}",
            f"analysis_confidence={max(0.0, min(1.0, analysis.confidence)):.3f}",
            f"evidence_count={evidence['evidence_count']}",
            f"risk_score={risk['score']}",
            f"reasoning_coherent={str(reasoning['coherent']).lower()}",
        ]
        rationale.extend(reasons)

        return JudgementReport(
            output_state=output_state,
            quality_score=quality,
            confidence_score=round(max(0.0, min(1.0, analysis.confidence)), 3),
            risk_score=int(risk["score"]),
            evidence_count=int(evidence["evidence_count"]),
            blocking_findings=tuple(risk["blocking_findings"]),
            review_reasons=reasons,
            rationale=tuple(rationale),
            human_review_required=output_state == OutputState.REVIEW_REQUIRED,
        )
