"""Bounded consequence simulation for complex or high-impact requests."""

from __future__ import annotations

import hashlib
import json
from typing import ClassVar

from oap.contracts import (
    BrainRequest,
    IntegratedAnalysis,
    OutputState,
    SafetyDecision,
    WarRoomReport,
)


class WarRoomEngine:
    """Produce deterministic review evidence without approval or execution power."""

    _SIGNAL_RISK: ClassVar[dict[str, int]] = {
        "GREEN": 10,
        "YELLOW": 40,
        "ORANGE": 70,
        "RED": 100,
        "WHITE": 5,
    }

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
                review_id=self._review_id(request, output_state),
                review_level="ROUTINE",
                risk_score=self._risk_score(request, analysis, safety),
                confidence_score=self._confidence_score(analysis),
                findings=self._findings(request, analysis, safety),
                requires_human_approval=output_state != OutputState.SYSTEM_LOG_ONLY,
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
            review_id=self._review_id(request, output_state),
            review_level="BLOCKED" if not safety.passed else "ENHANCED",
            risk_score=self._risk_score(request, analysis, safety),
            confidence_score=self._confidence_score(analysis),
            findings=self._findings(request, analysis, safety),
            requires_human_approval=True,
        )

    def _risk_score(
        self,
        request: BrainRequest,
        analysis: IntegratedAnalysis,
        safety: SafetyDecision,
    ) -> int:
        score = self._SIGNAL_RISK[safety.signal_level.value]
        if request.high_impact:
            score += 20
        if analysis.confidence < 0.5:
            score += 15
        if not safety.passed:
            score = 100
        return min(score, 100)

    @staticmethod
    def _confidence_score(analysis: IntegratedAnalysis) -> int:
        return round(min(max(analysis.confidence, 0.0), 1.0) * 100)

    @staticmethod
    def _findings(
        request: BrainRequest,
        analysis: IntegratedAnalysis,
        safety: SafetyDecision,
    ) -> tuple[str, ...]:
        findings = [finding.message for finding in safety.findings]
        if request.high_impact:
            findings.append("High-impact request requires enhanced consequence review.")
        if analysis.confidence < 0.5:
            findings.append("Analysis confidence is below the War Room threshold.")
        if not findings:
            findings.append("No blocking Guardian finding was reported.")
        return tuple(dict.fromkeys(findings))

    @staticmethod
    def _review_id(request: BrainRequest, output_state: OutputState) -> str:
        canonical = json.dumps(
            {
                "request_id": request.request_id,
                "task_type": request.task_type,
                "high_impact": request.high_impact,
                "output_state": output_state.value,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        return "WR-" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]

    def status(self) -> dict[str, object]:
        return {
            "component": "War Room",
            "ready": True,
            "mode": "simulation_only",
            "decision_authority": False,
            "structured_risk_score": True,
            "deterministic_review_id": True,
            "human_approval_final": True,
        }
