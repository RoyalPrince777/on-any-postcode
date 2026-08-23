"""Translate safety and integrated analysis into an allowed SMI output state."""

from __future__ import annotations

from oap.contracts import (
    BrainRequest,
    CoherenceReport,
    IntegratedAnalysis,
    OutputState,
    SafetyDecision,
    SignalLevel,
)


class JudgeEngine:
    def decide(
        self,
        request: BrainRequest,
        analysis: IntegratedAnalysis,
        safety: SafetyDecision,
        coherence: CoherenceReport | None = None,
    ) -> OutputState:
        if not safety.passed or safety.signal_level in {
            SignalLevel.ORANGE,
            SignalLevel.RED,
        }:
            return OutputState.BLOCK_REQUEST
        if request.task_type == OutputState.SYSTEM_LOG_ONLY.value:
            return OutputState.SYSTEM_LOG_ONLY
        if (
            request.high_impact
            or safety.human_review_required
            or analysis.signal_level == SignalLevel.YELLOW
            or (coherence is not None and coherence.review_required)
        ):
            return OutputState.REVIEW_REQUIRED
        return OutputState.RECOMMENDATION_READY
