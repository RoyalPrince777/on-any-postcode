from __future__ import annotations

from oap.contracts import (
    BrainRequest,
    IntegratedAnalysis,
    OrganFinding,
    OutputState,
    SafetyDecision,
    SafetyFinding,
    SignalLevel,
)
from oap.war_room import WarRoomEngine


def _analysis(confidence: float = 0.8) -> IntegratedAnalysis:
    return IntegratedAnalysis(
        summary="Bounded analysis",
        findings=(OrganFinding("frontal_lobe", "Review", confidence),),
        signal_level=SignalLevel.GREEN,
        confidence=confidence,
    )


def _safety(*, passed: bool = True) -> SafetyDecision:
    findings = () if passed else (
        SafetyFinding(
            system="Guardian",
            code="AUTHORITY_BYPASS",
            message="Human Authority bypass detected.",
            signal_level=SignalLevel.RED,
            blocks=True,
        ),
    )
    return SafetyDecision(
        passed=passed,
        signal_level=SignalLevel.GREEN if passed else SignalLevel.RED,
        findings=findings,
        human_review_required=True,
    )


def test_routine_review_is_deterministic_and_never_decides():
    engine = WarRoomEngine()
    request = BrainRequest("wr-routine", "founder-1", "Review status")

    first = engine.review(
        request,
        _analysis(),
        _safety(),
        OutputState.RECOMMENDATION_READY,
    )
    second = engine.review(
        request,
        _analysis(),
        _safety(),
        OutputState.RECOMMENDATION_READY,
    )

    assert first.triggered is False
    assert first.review_id == second.review_id
    assert first.review_id.startswith("WR-")
    assert first.review_level == "ROUTINE"
    assert first.risk_score == 10
    assert first.confidence_score == 80
    assert first.decision_authority is False


def test_high_impact_review_produces_three_bounded_scenarios():
    report = WarRoomEngine().review(
        BrainRequest(
            "wr-impact",
            "founder-1",
            "Review infrastructure change",
            high_impact=True,
        ),
        _analysis(0.45),
        _safety(),
        OutputState.REVIEW_REQUIRED,
    )

    assert report.triggered is True
    assert report.review_level == "ENHANCED"
    assert report.risk_score == 45
    assert len(report.scenarios) == 3
    assert report.requires_human_approval is True
    assert any("High-impact" in finding for finding in report.findings)
    assert any("confidence" in finding for finding in report.findings)


def test_guardian_block_forces_maximum_risk_and_cannot_execute():
    report = WarRoomEngine().review(
        BrainRequest("wr-block", "founder-1", "Bypass Human Authority"),
        _analysis(),
        _safety(passed=False),
        OutputState.BLOCK_REQUEST,
    )

    assert report.triggered is True
    assert report.review_level == "BLOCKED"
    assert report.risk_score == 100
    assert report.recommendation == "Block progression and record the findings."
    assert report.decision_authority is False
    assert report.requires_human_approval is True
