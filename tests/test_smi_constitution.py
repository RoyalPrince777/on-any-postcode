from mission_control.smi_constitution import (
    BODY_LAWS,
    MIND_LAWS,
    REVIEW_DEPTHS,
    SMI_ANATOMY,
    SMI_HIERARCHY,
    SOUL_LAWS,
    TWENTY_ONE_LAWS,
    WAR_ROOM_CYCLE,
    constitution_status,
    review_depth,
)


def test_constitution_is_exactly_seven_seven_seven():
    assert len(MIND_LAWS) == 7
    assert len(BODY_LAWS) == 7
    assert len(SOUL_LAWS) == 7
    assert len(TWENTY_ONE_LAWS) == 21
    assert len(set(TWENTY_ONE_LAWS)) == 21


def test_smi_is_highest_intelligence_but_human_authority_is_final():
    assert SMI_HIERARCHY[:3] == ("Human Authority", "SMI", "Living Kernel")
    status = constitution_status()
    assert status["highest_intelligence"] == "SMI"
    assert status["final_authority"] == "Human Authority"
    assert status["living_kernel_subordinate"] is True


def test_review_depth_escalates_and_critical_forces_21():
    assert REVIEW_DEPTHS == (3, 7, 21)
    assert review_depth() == 3
    assert review_depth(consequential=True) == 7
    assert review_depth(critical=True) == 21
    assert review_depth(consequential=True, critical=True) == 21


def test_war_room_has_no_independent_authority():
    assert SMI_ANATOMY["War Room"].startswith("SMI command")
    assert constitution_status()["war_room_is_command_surface"] is True
    assert constitution_status()["authority_transfer_by_agent_cooperation"] is False


def test_learning_cannot_self_promote_to_production():
    assert "Oasis" in WAR_ROOM_CYCLE
    assert constitution_status()["oasis_auto_promote"] is False


def test_guardian_precedes_human_authority_and_execution():
    guardian = WAR_ROOM_CYCLE.index("Guardian")
    human = WAR_ROOM_CYCLE.index("Human Authority")
    execution = WAR_ROOM_CYCLE.index("Execution")
    assert guardian < human < execution
