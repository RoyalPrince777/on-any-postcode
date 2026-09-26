import pytest

from mission_control import all_in_ai_runtime


def test_runtime_reuses_single_smi_brain_and_general_intelligence_spine():
    state = all_in_ai_runtime.status()
    assert state["ready"] is True
    assert state["brain_count_added"] == 0
    assert state["single_smi_brain_preserved"] is True
    assert state["agi_core_ready"] is True
    assert state["general_intelligence_capabilities"] == 15
    assert state["independent_execute"] is False
    assert state["independent_approval"] is False
    assert state["human_authority_final"] is True


def test_mission_routes_through_existing_agi_and_command_intelligence():
    plan = all_in_ai_runtime.plan_mission(
        "Deep dive OAP Maps movement routing and recovery",
        task_type="TECHNICAL",
    )
    binding = plan["smi_binding"]
    assert binding["brain_count_added"] == 0
    assert binding["single_smi_brain_preserved"] is True
    assert "movement" in binding["agi_route"]["world_ids"]
    assert binding["command_review"]["core_path"][0] == "agi"
    assert binding["command_review"]["command_path"] == (
        "sgi",
        "tgi",
        "ogi",
        "dgi",
        "pgi",
        "rgi",
        "adgi",
        "mgi",
    )
    assert plan["red_team"]["fail_closed_without_evidence"] is True
    assert plan["truth_mode"]["execution_granted"] is False
    assert plan["authority"]["founder_final"] is True


def test_alien_research_mode_stays_speculative_and_non_executing():
    plan = all_in_ai_runtime.plan_mission(
        "Explore an unconventional future communications architecture",
        research_mode="alien_research",
    )
    assert plan["alien_research"]["active"] is True
    assert plan["alien_research"]["claims_fact_without_evidence"] is False
    assert plan["alien_research"]["requires_truth_mode_evidence"] is True
    assert plan["alien_research"]["execution_authority"] is False


@pytest.mark.parametrize("mission", ["", "   ", None])
def test_empty_mission_fails_closed(mission):
    with pytest.raises(ValueError, match="mission_required"):
        all_in_ai_runtime.plan_mission(mission)


def test_unknown_research_mode_fails_closed():
    with pytest.raises(ValueError, match="unsupported_research_mode"):
        all_in_ai_runtime.plan_mission("test", research_mode="magic")
