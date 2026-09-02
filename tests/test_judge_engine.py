from oap.contracts import (
    BrainRequest,
    IntegratedAnalysis,
    OrganFinding,
    OutputState,
    SafetyDecision,
    SafetyFinding,
    SignalLevel,
)
from oap.smi.judge_engine import JudgeEngine


def _request(*, high_impact=False, task_type="GENERAL"):
    return BrainRequest(
        request_id="judge-test",
        identity_id="founder",
        content="review this",
        task_type=task_type,
        high_impact=high_impact,
    )


def _analysis(*, level=SignalLevel.GREEN, confidence=0.9, findings=True):
    items = ()
    if findings:
        items = (
            OrganFinding(
                organ_id="frontal_lobe",
                summary="Reasoned option is bounded and reversible.",
                confidence=0.9,
                signal_level=level,
            ),
        )
    return IntegratedAnalysis(
        summary="Integrated review" if findings else "",
        findings=items,
        signal_level=level,
        confidence=confidence,
    )


def _safety(*, passed=True, level=SignalLevel.GREEN, review=False, blocks=False):
    findings = ()
    if blocks:
        findings = (
            SafetyFinding(
                system="Aegis",
                code="blocked",
                message="Aegis blocked the request.",
                signal_level=level,
                blocks=True,
            ),
        )
    return SafetyDecision(
        passed=passed,
        signal_level=level,
        findings=findings,
        human_review_required=review,
    )


def test_green_evidence_backed_request_is_recommendation_only():
    report = JudgeEngine().review(_request(), _analysis(), _safety())

    assert report.output_state == OutputState.RECOMMENDATION_READY
    assert report.can_execute is False
    assert report.evidence_count == 1
    assert report.quality_score > 0.8
    assert report.human_review_required is False


def test_high_impact_request_requires_human_review():
    report = JudgeEngine().review(
        _request(high_impact=True),
        _analysis(),
        _safety(),
    )

    assert report.output_state == OutputState.REVIEW_REQUIRED
    assert report.human_review_required is True
    assert "high_impact_request" in report.review_reasons


def test_failed_or_orange_safety_fails_closed():
    report = JudgeEngine().review(
        _request(),
        _analysis(),
        _safety(passed=False, level=SignalLevel.ORANGE, blocks=True),
    )

    assert report.output_state == OutputState.BLOCK_REQUEST
    assert "Aegis:blocked" in report.blocking_findings
    assert report.risk_score >= 3


def test_orange_analysis_cannot_become_ready_even_when_safety_is_green():
    report = JudgeEngine().review(
        _request(),
        _analysis(level=SignalLevel.ORANGE),
        _safety(),
    )

    assert report.output_state == OutputState.BLOCK_REQUEST
    assert "analysis_signal_orange" in report.review_reasons


def test_missing_analysis_evidence_requires_review():
    report = JudgeEngine().review(
        _request(),
        _analysis(findings=False, confidence=0.0),
        _safety(),
    )

    assert report.output_state == OutputState.REVIEW_REQUIRED
    assert "analysis_summary_missing" in report.review_reasons
    assert "analysis_evidence_missing" in report.review_reasons


def test_system_log_only_preserves_existing_output_contract():
    output = JudgeEngine().decide(
        _request(task_type=OutputState.SYSTEM_LOG_ONLY.value),
        _analysis(),
        _safety(),
    )

    assert output == OutputState.SYSTEM_LOG_ONLY
