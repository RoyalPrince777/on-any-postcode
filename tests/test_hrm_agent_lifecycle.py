from mission_control.hrm_agent_lifecycle import (
    LifecycleDirection,
    ReviewDepth,
    assess_agent,
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


def test_low_risk_uses_three_step_review():
    assert required_depth(risk="low") is ReviewDepth.QUICK


def test_medium_risk_escalates_to_seven_steps():
    assert required_depth(risk="medium") is ReviewDepth.COUNCIL


def test_authority_change_always_uses_full_21_steps():
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
