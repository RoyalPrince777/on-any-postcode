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
    AgentRank,
    TRAINING_25_8,
    assess_agent,
    lifecycle_plan,
    rank_for_strength,
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


def test_rank_thresholds_are_truth_bounded_and_ordered():
    assert rank_for_strength(20) is AgentRank.TRAINEE
    assert rank_for_strength(70) is AgentRank.SPECIALIST
    assert rank_for_strength(80) is AgentRank.SENIOR
    assert rank_for_strength(90) is AgentRank.ELITE
    assert rank_for_strength(98) is AgentRank.CAPTAIN


def test_missing_full_evidence_forces_learning_not_promotion():
    plan = lifecycle_plan(
        100,
        evidence_coverage_percent=85,
        current_rank=AgentRank.SPECIALIST,
    )
    assert plan["direction"] == LifecycleDirection.LEARN.value
    assert plan["recommended_rank"] == AgentRank.SPECIALIST.value
    assert plan["promotion_candidate"] is False
    assert plan["automatic_rank_change_allowed"] is False


def test_promotion_advances_only_one_rank_and_requires_human_authority():
    plan = lifecycle_plan(
        96,
        evidence_coverage_percent=100,
        current_rank=AgentRank.SPECIALIST,
    )
    assert plan["direction"] == LifecycleDirection.PROMOTE.value
    assert plan["recommended_rank"] == AgentRank.SENIOR.value
    assert plan["human_authority_required"] is True
    assert plan["automatic_rank_change_allowed"] is False


def test_downgrade_is_one_rank_at_a_time_and_helper_review_is_recommended():
    plan = lifecycle_plan(
        60,
        evidence_coverage_percent=100,
        current_rank=AgentRank.ELITE,
    )
    assert plan["direction"] == LifecycleDirection.DOWNGRADE.value
    assert plan["recommended_rank"] == AgentRank.SENIOR.value
    assert plan["helper_review_recommended"] is True
    assert plan["human_authority_required"] is True


def test_severe_failure_suspends_before_any_termination():
    plan = lifecycle_plan(
        99,
        evidence_coverage_percent=100,
        current_rank=AgentRank.CAPTAIN,
        risk="critical",
        material_failures=3,
    )
    assert plan["direction"] == LifecycleDirection.SUSPEND.value
    assert plan["termination_candidate"] is False
    assert plan["helper_review_recommended"] is True


def test_termination_is_candidate_only_and_never_automatic():
    plan = lifecycle_plan(
        20,
        evidence_coverage_percent=100,
        current_rank=AgentRank.TRAINEE,
        termination_requested=True,
    )
    assert plan["direction"] == LifecycleDirection.TERMINATE_CANDIDATE.value
    assert plan["human_authority_required"] is True
    assert plan["automatic_rank_change_allowed"] is False


def test_25_8_training_is_brand_shorthand_not_fake_time_claim():
    assert TRAINING_25_8["name"] == "25-8 Training"
    assert TRAINING_25_8["mode"] == "continuous_event_driven_learning"
    assert TRAINING_25_8["literal_time_claim"] is False
    assert TRAINING_25_8["first_party_only"] is True
    assert TRAINING_25_8["self_promotion_allowed"] is False
    assert TRAINING_25_8["self_termination_allowed"] is False
