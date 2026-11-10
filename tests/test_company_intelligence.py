from mission_control import company_intelligence


def test_protocol_is_700_checks_not_700_stop_start_stages():
    status = company_intelligence.status()

    assert status["review_area_count"] == 7
    assert status["intelligence_lens_count"] == 10
    assert status["evidence_test_count"] == 10
    assert status["protocol_check_count"] == 700
    assert status["protocol_is_checks_not_stages"] is True
    assert len(company_intelligence.protocol_cells()) == 700
    assert len(set(company_intelligence.protocol_cells())) == 700


def test_company_intelligence_covers_music_clothing_and_print_on_demand():
    status = company_intelligence.status()

    assert status["commercial_lanes"] == ("music", "clothing", "print_on_demand")
    assert status["music_policy"]["distribution_scope"] == "OAP-only"
    assert status["music_policy"]["external_platform_distribution"] is False
    assert status["music_policy"]["external_distribution_future_assumption"] is False
    assert status["music_policy"]["direct_purchase_primary"] is True
    assert status["music_policy"]["minimum_track_price_gbp"] == 1
    assert status["print_on_demand_policy"]["is_production_method_not_separate_brand"] is True
    assert status["print_on_demand_policy"]["oap_market_front_door"] is True


def test_hormozi_intelligence_is_cross_oap_commercial_review_not_execution_authority():
    plan = company_intelligence.review_plan("music")

    assert plan["scope"] == "whole_oap_world"
    assert len(plan["hormozi_intelligence"]) == 7
    assert tuple(item["id"] for item in plan["hormozi_intelligence"]) == (
        "dream_outcome",
        "perceived_likelihood",
        "time_delay",
        "effort_sacrifice",
        "offer_stack",
        "price_value_gap",
        "unit_economics",
    )
    assert plan["votes_grant_execution"] is False
    assert plan["external_action_taken"] is False
    assert plan["founder_final_required"] is True
    assert plan["full_green"] is False


def test_existing_red_team_matrix_agents_are_reused_not_reinvented():
    status = company_intelligence.status()
    plan = company_intelligence.review_plan("clothing")
    participants = set(plan["review_agents"]) | set(plan["canonical_judges"])

    for name in (
        "Bagheera",
        "Shere Khan",
        "Agent Smith",
        "Twinz",
        "Neo",
        "Morpheus",
        "Trinity",
        "Oracle",
        "Architect",
        "Keymaker",
        "Seraph",
    ):
        assert name in participants

    assert status["matrix_participants_reused"] is True
    assert status["canonical_judges_reused"] is True
    assert status["guardian_and_green_gate_separate"] is True


def test_votes_require_named_reviewer_and_evidence_and_never_grant_authority():
    result = company_intelligence.tally_attributable_votes(
        (
            {
                "reviewer": "Bagheera",
                "decision": "PASS",
                "evidence": "rights-register:test-1",
            },
            {
                "reviewer": "Twinz",
                "decision": "CONDITIONAL",
                "evidence": "supplier-proof:test-2",
            },
            {
                "reviewer": "Unknown Agent",
                "decision": "PASS",
                "evidence": "made-up",
            },
            {
                "reviewer": "Shere Khan",
                "decision": "PASS",
                "evidence": "",
            },
        )
    )

    assert result["attributable_vote_count"] == 2
    assert result["counts"]["PASS"] == 1
    assert result["counts"]["CONDITIONAL"] == 1
    assert len(result["rejected"]) == 2
    assert result["votes_grant_execution"] is False
    assert result["founder_final_required"] is True


def test_truth_boundaries_remain_fail_closed():
    status = company_intelligence.status()

    assert status["legal_authority_claimed"] is False
    assert status["regulatory_permission_claimed"] is False
    assert status["production_execution_granted"] is False
    assert status["human_authority_final"] is True
    assert status["full_green"] is False
