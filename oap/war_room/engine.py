"""Bounded consequence simulation for complex or high-impact requests."""

from __future__ import annotations

from oap.contracts import (
    BrainRequest,
    IntegratedAnalysis,
    OutputState,
    SafetyDecision,
    WarRoomReport,
)


class WarRoomEngine:
    def review(
        self,
        request: BrainRequest,
        analysis: IntegratedAnalysis,
        safety: SafetyDecision,
        output_state: OutputState,
    ) -> WarRoomReport:
        triggered = request.high_impact or output_state in {
            OutputState.REVIEW_REQUIRED,
            OutputState.BLOCK_REQUEST,
        }
        if not triggered:
            return WarRoomReport(
                triggered=False,
                scenarios=(),
                recommendation="Standard Human Authority review remains required.",
            )

        scenarios = (
            "Proceed only after verified authority and reversible controls.",
            "Delay while missing evidence, permissions or provider backing is resolved.",
            "Reject if Guardian findings remain blocking or irreversible.",
        )
        recommendation = (
            "Block progression and record the findings."
            if not safety.passed
            else (
                "Human Authority should compare benefit, risk and reversibility; "
                f"internal confidence is {analysis.confidence:.0%}."
            )
        )
        return WarRoomReport(
            triggered=True,
            scenarios=scenarios,
            recommendation=recommendation,
        )

    def status(self) -> dict[str, object]:
        return {
            "component": "War Room",
            "ready": True,
            "mode": "simulation_only",
            "decision_authority": False,
        }
