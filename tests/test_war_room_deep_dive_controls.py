from __future__ import annotations

from mission_control import war_room_simulation_actions


def test_deep_dive_action_catalogue_is_bounded_and_human_authority_final():
    catalogue = war_room_simulation_actions.list_actions()
    action_ids = {item["id"] for item in catalogue["actions"]}

    assert catalogue["mode"] == "dry_run_preview_only"
    assert catalogue["stage_count"] == 21
    assert len(catalogue["review_lenses"]) == 7
    assert len(catalogue["baseline_judge_panel"]) == 7
    assert catalogue["human_authority_final"] is True
    assert catalogue["overall_green"] is False
    assert {
        "run_war_room",
        "deep_dive_21",
        "agent_advisory",
        "auto_select_7",
        "red_team",
        "dependency_scan",
        "failure_test",
        "guardian_check",
        "hrm_check",
        "recovery_test",
        "next_gate",
        "score_7x",
        "strongest_link",
        "weakest_link",
        "minority_report",
        "judge_speeches",
    } <= action_ids
    assert catalogue["global_locks"] == {
        "payment_capture_enabled": False,
        "dispatch_enabled": False,
        "hidden_tracking_enabled": False,
        "self_approval_enabled": False,
        "agi_or_asi_claim_enabled": False,
    }


def test_deep_dive_21_stays_learning_and_review_only():
    result = war_room_simulation_actions.simulate(
        "deep_dive_21", "SMI infrastructure recovery", 21
    )

    assert result["depth"] == 21
    assert result["war_room_signal"] == "🟡"
    assert result["learning_signal"] == "🟣"
    assert result["stage"]["progress"] == "21/21"
    assert result["judge_count"] == 7
    assert "Neo" in result["judge_panel"]
    assert result["result"]["safe_to_execute"] is False
    assert result["result"]["overall_green"] is False
    assert result["private_chain_of_thought_exposed"] is False
    assert result["human_authority_final"] is True


def test_auto_select_7_adapts_one_registered_specialist_seat():
    dependency = war_room_simulation_actions.simulate(
        "auto_select_7", "NEXUS dependency cascade", "auto"
    )
    evidence = war_room_simulation_actions.simulate(
        "auto_select_7", "precision evidence proof review", "auto"
    )

    assert len(dependency["judge_panel"]) == 7
    assert "Spider" in dependency["judge_panel"]
    assert "Falcon" in evidence["judge_panel"]
    roster = set(war_room_simulation_actions.REGISTERED_ADVISORY_ROSTER)
    assert set(dependency["judge_panel"]) <= roster
    assert set(evidence["judge_panel"]) <= roster


def test_requested_agent_must_match_registered_control_roster():
    neo = war_room_simulation_actions.simulate(
        "agent_advisory", "Neo | recovery review", "auto"
    )
    unknown = war_room_simulation_actions.simulate(
        "agent_advisory", "Unknown Agent | recovery review", "auto"
    )

    assert neo["agent_request"] == {
        "requested": "Neo",
        "registered_for_control": True,
        "canonical_name": "Neo",
        "authority": "advisory_only",
    }
    assert unknown["agent_request"]["registered_for_control"] is False
    assert unknown["agent_request"]["canonical_name"] is None
    assert unknown["result"]["safe_to_execute"] is False


def test_war_room_page_exposes_safe_command_buttons_only(client):
    response = client.get("/mission/war-room")
    page = response.get_data(as_text=True)

    assert response.status_code == 200
    for label in (
        "RUN WAR ROOM",
        "DEEP DIVE 21",
        "BRING IN AGENT",
        "AUTO SELECT 7",
        "SHOW EVIDENCE",
        "SHOW THINKING",
        "RED TEAM",
        "DEPENDENCIES",
        "FAILURE TEST",
        "GUARDIAN CHECK",
        "HRM CHECK",
        "RECOVERY TEST",
        "SCORE 7×",
        "STRONGEST LINK",
        "WEAKEST LINK",
        "MINORITY REPORT",
        "JUDGE SPEECHES",
        "NEXT GATE",
    ):
        assert label in page

    assert "Deep-Dive Command Deck" in page
    assert "Telemetry, never private thoughts" in page
    assert "never exposes hidden prompts" in page
    assert "/mission/smi/simulate" in page
    assert "/mission/smi/thinking-signals" in page
    assert 'method="post"' not in page.lower()
