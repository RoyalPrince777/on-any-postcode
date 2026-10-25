from mission_control.complementary_intelligence_review import (
    complementary_intelligence_review,
)


def test_complementary_review_preserves_registry_and_does_not_invent_ids():
    result = complementary_intelligence_review()
    assert result["mode"] == "read_only"
    assert not result["new_agent_ids_issued"]
    assert not result["registry_mutated"]
    assert not result["execution_authorised"]
    assert result["founder_final_required"]
    assert not result["gender_based_role_assignment"]
    by_capability = {pair["capability"]: pair for pair in result["pairs"]}
    tiger = by_capability["tiger"]["identities"]
    assert tiger[0]["agent_id"] == "JUNGLE-SHERE-KHAN-001"
    assert tiger[1]["agent_id"] == "ANIMAL-TIGER-001"
    for pair in result["pairs"]:
        assert not pair["pairing_verified"]
        assert pair["distinct_roles_review_required"]
        for agent in pair["identities"]:
            if not agent["registered"]:
                assert agent["agent_id"] is None
