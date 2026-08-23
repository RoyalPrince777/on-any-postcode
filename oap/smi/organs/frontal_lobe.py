"""Executive recommendation formation without execution authority."""

from __future__ import annotations

from oap.contracts import IntegratedAnalysis, SafetyDecision


class FrontalLobe:
    organ_id = "frontal_lobe"

    def form_summary(
        self,
        task_type: str,
        analysis: IntegratedAnalysis,
        safety: SafetyDecision,
    ) -> tuple[str, tuple[str, ...]]:
        summary = (
            f"SMI completed {task_type} analysis at "
            f"{analysis.confidence:.0%} internal confidence."
        )
        rationale = [analysis.summary]
        rationale.extend(item.summary for item in analysis.findings)
        rationale.extend(finding.message for finding in safety.findings)
        return summary, tuple(rationale)
