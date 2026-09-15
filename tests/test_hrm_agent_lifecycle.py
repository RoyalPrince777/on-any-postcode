from mission_control.hrm_agent_lifecycle import (
    BODY_7,
    CANONICAL_GOVERNANCE,
    GOVERNANCE_777,
    MIND_7,
    SOUL_7,
    TOTAL_GOVERNED_CHECKS,
    GovernancePlane,
    LifecycleDirection,
    ReviewDepth,
    assess_agent,
    governance_checks,
    required_depth,
    stars_for_score,
)


def test_score_maps_to_seven_star_scale():
    assert stars_for_score(100) == 7
    assert stars_for_score(94) == 6
    assert stars_for_score(80) == 5
    assert stars_for_score(70) == 4
    assert stars_for_score(60) == 3
    assert stars_for_score(45) == 2
    assert stars_for_score(20) == 1


def test_canonical_governance_is_seven_seven_seven():
    assert CANONICAL_GOVERNANCE == "7-7-7"
    assert len(MIND_7) == 7
    assert len(BODY_7) == 7
    assert len(SOUL_7) == 7
    assert TOTAL_GOVERNED_CHECKS == 21


def test_every_governed_signal_keeps_mind_body_soul():
    checks = governance_checks(risk="low")
    assert checks == GOVERNANCE_777
    assert tuple(checks) == (
        GovernancePlane.MIND,
        GovernancePlane.BODY,
        GovernancePlane.SOUL,
    )
    assert all(len(plane_checks) == 7 for plane_checks in checks.values())


def test_high_risk_keeps_all_21_checks():
    checks = governance_checks(risk="critical")
    assert sum(len(plane_checks) for plane_checks in checks.values()) == 21


def test_legacy_depth_selector_remains_compatible():
    assert required_depth(risk="low") is ReviewDepth.QUICK
    assert required_depth(risk="medium") is ReviewDepth.COUNCIL
    assert required_depth(risk="low", authority_change=True) is ReviewDepth.FULL


def test_promotion_is_recommendation_requiring_human_authority():
    result = assess_agent(92, promotion_candidate=True)
    assert result.direction is LifecycleDirection.PROMOTE
    assert result.depth is ReviewDepth.FULL
    assert result.human_authority_required is True
    assert result.fail_closed is False


def test_termination_is_candidate_not_automatic_deletion():
    result = assess_agent(30, risk="critical", termination_candidate=True)
    assert result.direction is LifecycleDirection.TERMINATE_CANDIDATE
    assert result.depth is ReviewDepth.FULL
    assert result.human_authority_required is True
    assert result.fail_closed is True


def test_severe_risk_can_fail_closed_without_promoting_authority():
    result = assess_agent(96, risk="high")
    assert result.direction is LifecycleDirection.SUSPEND
    assert result.fail_closed is True
    assert result.human_authority_required is False
