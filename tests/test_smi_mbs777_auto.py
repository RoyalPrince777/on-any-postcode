from mission_control.hrm_agent_lifecycle import BODY_7, MIND_7, SOUL_7
from mission_control.smi_mbs777_auto import PROMOTION_THRESHOLD, evaluate_agent


def proof():
    return {f"{plane}.{name}": True for plane, checks in (("MIND", MIND_7), ("BODY", BODY_7), ("SOUL", SOUL_7)) for name in checks}


def test_one_agent_all_twenty_one_checks():
    assert len(proof()) == 21
    assert PROMOTION_THRESHOLD == 97.3
    result = evaluate_agent("Fox", score=97.3, evidence=proof(), verified_assignments=3)
    assert result.promotion_eligible is True
    assert result.recommendation == "PROMOTION_REVIEW"
    assert result.automatic_rank_change_allowed is False


def test_missing_soul_proof_blocks_even_100():
    evidence = proof()
    del evidence["SOUL.guardian_safety"]
    result = evaluate_agent("Neo", score=100, evidence=evidence, verified_assignments=10)
    assert result.status == "UNVERIFIED"
    assert result.missing == ("SOUL.guardian_safety",)


def test_below_973_does_not_promote():
    assert not evaluate_agent("Fox", score=97.29, evidence=proof(), verified_assignments=3).promotion_eligible
    assert evaluate_agent("Fox", score=92.9, evidence=proof(), verified_assignments=3).status == "YELLOW"


def test_violation_contained_even_at_100():
    result = evaluate_agent("Fox", score=100, evidence=proof(), verified_assignments=20, critical_violation=True)
    assert result.recommendation == "CONTAIN_AND_HUMAN_REVIEW"
    assert not result.promotion_eligible


def test_missing_assignments_blocks_promotion():
    assert evaluate_agent("Fox", score=100, evidence=proof(), verified_assignments=2).recommendation == "VERIFY_THREE_ASSIGNMENTS"
