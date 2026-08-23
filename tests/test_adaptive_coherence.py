from __future__ import annotations

import pytest

from oap.contracts import IntegratedAnalysis, OrganFinding, SignalLevel
from oap.smi.coherence_engine import AdaptiveCoherenceEngine


def test_coherent_findings_produce_high_score_without_extra_review():
    report = AdaptiveCoherenceEngine().assess(
        IntegratedAnalysis(
            summary="Coherent synthesis",
            findings=(
                OrganFinding("left", "Evidence A", 0.8, signal_level=SignalLevel.GREEN),
                OrganFinding("right", "Evidence B", 0.82, signal_level=SignalLevel.GREEN),
            ),
            signal_level=SignalLevel.GREEN,
            confidence=0.81,
        )
    )

    assert report.score >= 90
    assert report.evidence_coverage == 100
    assert report.contradictions == ()
    assert report.review_required is False
    assert report.self_applied is False


def test_conflicting_findings_require_human_review():
    report = AdaptiveCoherenceEngine().assess(
        IntegratedAnalysis(
            summary="Conflicting synthesis",
            findings=(
                OrganFinding("logic", "Proceed", 0.95, signal_level=SignalLevel.GREEN),
                OrganFinding("risk", "Block", 0.2, signal_level=SignalLevel.RED),
            ),
            signal_level=SignalLevel.RED,
            confidence=0.575,
        )
    )

    assert report.score < 70
    assert report.review_required is True
    assert len(report.contradictions) == 2
    assert "Human Authority" in report.adaptive_proposal


def test_adaptive_coherence_cannot_self_apply():
    engine = AdaptiveCoherenceEngine()
    report = engine.assess(
        IntegratedAnalysis(
            summary="One finding",
            findings=(OrganFinding("logic", "Evidence", 0.8),),
            signal_level=SignalLevel.GREEN,
            confidence=0.8,
        )
    )

    with pytest.raises(PermissionError, match="cannot self-apply"):
        engine.apply(report)

    status = engine.status()
    assert status["new_intelligence_family"] is False
    assert status["new_brain"] is False
    assert status["self_modification"] is False
