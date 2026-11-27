from mission_control import agents, ai_behaviour_protocol


def test_matrix_brothers_selected_for_native_handoff_without_new_passports():
    original = next(
        item for item in agents.MATRIX_ADVISORY_ALLIANCES
        if item["id"] == "tank_dozer_brothers"
    )
    assert original["members"] == ("Tank", "Dozer")
    plan = ai_behaviour_protocol.recommend_agent_team("Recover native SMI execution")
    assert tuple(row["name"] for row in plan["active_team"]) == (
        "Tank", "Dozer", "Bagheera",
    )
    assert all(row["authority"] == "advisory_review_only" for row in plan["active_team"])
    assert "Guardian" in plan["mandatory_gates_unchanged"]
    assert agents.MATRIX_ALLIANCE_POLICY["execution"] == "DISABLED"


def test_brothers_strength_stays_unrated_without_evidence():
    for name in ("Tank", "Dozer"):
        row = ai_behaviour_protocol.agent_strength_status(name)
        assert row["proven_strength_percent"] is None
        assert row["measured_strength_percent"] is None
        assert row["strength_light"] == "purple"
        assert row["evidence_coverage_percent"] == 0
