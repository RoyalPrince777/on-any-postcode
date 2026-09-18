"""Regression tests for the EARTH IS OUR TURF Role Growth War Room."""

from oap.war_room.role_growth import (
    PROTOCOL_21,
    SEVEN_STAR_GATE,
    review_role_growth,
    status,
)


def _complete_evidence():
    evidence = {check_id: True for check_id, _, _ in PROTOCOL_21}
    evidence.update(
        {f"gate_{gate_id}": True for gate_id, _ in SEVEN_STAR_GATE}
    )
    evidence.update(
        {
            "no_self_certification": True,
            "duplicate_proof_detection": True,
            "independent_confirmation": True,
            "anti_collusion": True,
            "no_sika_only_promotion": True,
            "separation_of_duties": True,
        }
    )
    return evidence


def test_role_growth_war_room_is_advisory_and_fail_closed():
    result = review_role_growth({}, lane="president")

    assert result["decision_authority"] is False
    assert result["human_authority_final"] is True
    assert result["protocol_total"] == 21
    assert result["stars_total"] == 7
    assert result["can_recommend_promotion"] is False
    assert result["blockers"]
    assert result["gate_blockers"]
    assert result["anti_gaming"]["ready"] is False


def test_complete_sensitive_lane_can_only_be_referred_to_human_authority():
    result = review_role_growth(_complete_evidence(), lane="president")

    assert result["percent"] == 100
    assert result["stars"] == 7
    assert result["signal"] == "green"
    assert result["anti_gaming"]["ready"] is True
    assert result["can_recommend_promotion"] is True
    assert result["recommendation"] == "Evidence supports referral to Human Authority."
    assert result["decision_authority"] is False


def test_sika_or_protocol_success_cannot_bypass_anti_gaming():
    evidence = _complete_evidence()
    evidence["anti_collusion"] = False

    result = review_role_growth(evidence, lane="matrix")

    assert result["percent"] == 100
    assert result["stars"] == 7
    assert result["anti_gaming"]["ready"] is False
    assert result["can_recommend_promotion"] is False


def test_traditional_title_requires_separate_authentication():
    evidence = _complete_evidence()
    evidence["traditional_title_authenticated"] = False

    blocked = review_role_growth(evidence, lane="traditional_title")
    assert blocked["can_recommend_promotion"] is False

    evidence["traditional_title_authenticated"] = True
    reviewed = review_role_growth(evidence, lane="traditional_title")
    assert reviewed["traditional_title_authenticated"] is True
    assert reviewed["can_recommend_promotion"] is True


def test_ordinary_lane_does_not_require_human_gate_by_default():
    evidence = _complete_evidence()
    evidence["gate_human_gate"] = False

    result = review_role_growth(evidence, lane="learning")

    human_gate = next(
        gate for gate in result["seven_star_gate"] if gate["id"] == "human_gate"
    )
    assert human_gate["passed"] is True
    assert human_gate["evidence_state"] == "not_required"


def test_status_exposes_council_and_truth_boundaries():
    result = status()

    assert result["protocol_checks"] == 21
    assert result["gate_stars"] == 7
    assert result["decision_authority"] is False
    assert result["anti_gaming_fail_closed"] is True
    assert any(member["name"] == "Shere Khan" for member in result["council"])
    assert any(member["name"] == "Adam Smith" for member in result["council"])
    assert any(member["name"] == "Bagheera" for member in result["council"])
    assert any(member["name"] == "Akela" for member in result["council"])
    assert any(member["name"] == "Gyata / Lion" for member in result["council"])
