"""Adaptive coherence assessment without autonomous rule modification."""

from __future__ import annotations

from statistics import pstdev

from oap.contracts import CoherenceReport, IntegratedAnalysis, SignalLevel

_SEVERITY = {
    SignalLevel.WHITE: 0,
    SignalLevel.GREEN: 1,
    SignalLevel.YELLOW: 2,
    SignalLevel.ORANGE: 3,
    SignalLevel.RED: 4,
}


class AdaptiveCoherenceEngine:
    """Measure consistency and propose review; never alter rules or findings."""

    def assess(self, analysis: IntegratedAnalysis) -> CoherenceReport:
        findings = analysis.findings
        if not findings:
            return CoherenceReport(
                score=0,
                agreement_score=0,
                evidence_coverage=0,
                confidence_spread=100,
                contradictions=("No internal SMI findings were supplied.",),
                review_required=True,
                adaptive_proposal="Request additional evidence before recommendation.",
            )

        confidences = [min(max(item.confidence, 0.0), 1.0) for item in findings]
        levels = [_SEVERITY[item.signal_level] for item in findings]
        spread = round(pstdev(confidences) * 100) if len(confidences) > 1 else 0
        level_span = max(levels) - min(levels)
        agreement = max(0, 100 - spread - (level_span * 15))
        evidence = round(
            sum(bool(item.summary.strip()) and bool(item.organ_id.strip()) for item in findings)
            / len(findings)
            * 100
        )

        contradictions: list[str] = []
        if level_span >= 2:
            contradictions.append("Internal signal levels materially disagree.")
        if spread >= 25:
            contradictions.append("Internal confidence scores materially diverge.")
        if evidence < 100:
            contradictions.append("One or more findings lack attributable evidence.")

        score = round((agreement * 0.65) + (evidence * 0.35))
        review_required = score < 70 or bool(contradictions)
        proposal = (
            "Human Authority should request targeted evidence for the conflicting "
            "regions before approval."
            if review_required
            else "Preserve the current synthesis; continue bounded monitoring."
        )
        return CoherenceReport(
            score=score,
            agreement_score=agreement,
            evidence_coverage=evidence,
            confidence_spread=spread,
            contradictions=tuple(contradictions),
            review_required=review_required,
            adaptive_proposal=proposal,
        )

    def apply(self, report: CoherenceReport) -> None:
        del report
        raise PermissionError(
            "Adaptive Coherent Intelligence cannot self-apply a refinement"
        )

    def status(self) -> dict[str, object]:
        return {
            "component": "Adaptive Coherent Intelligence",
            "ready": True,
            "scope": "internal_smi_capability",
            "new_intelligence_family": False,
            "new_brain": False,
            "self_modification": False,
            "human_approval_final": True,
        }
