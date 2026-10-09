"""Agent passports remain descriptive and fail closed."""

import pytest

from mission_control.agent_passports import (
    MODES,
    agent_mode,
    agent_passport,
    passport_directory,
)


def test_seven_modes_shared_across_all_registered_agents():
    passports = passport_directory()
    assert len(MODES) == 7
    assert len(passports) == len({p.agent_id for p in passports})
    assert all(p.modes == MODES and not p.execution_authorised for p in passports)


def test_fox_remains_land_within_animal_intelligence():
    fox = agent_passport("fox")
    assert (fox.intelligence, fox.domain) == ("animal", "land")
    assert "routing" in fox.role


def test_octopus_and_matrix_keep_separate_domains():
    assert agent_passport("octopus").domain == "marine"
    assert agent_passport("neo").intelligence == "matrix"
    assert agent_passport("gorilla").intelligence == "animal"


def test_modes_do_not_activate_or_authorise_agents():
    for mode in MODES:
        result = agent_mode("Fox", mode)
        assert result["runtime_active"] is False
        assert result["execution_authorised"] is False


@pytest.mark.parametrize("agent,mode", [("unknown", "plan"), ("fox", "override")])
def test_unknown_agents_and_modes_rejected(agent, mode):
    with pytest.raises(ValueError):
        agent_mode(agent, mode)


def test_rank_movement_up_same_down():
    from mission_control.agent_passports import RANKS, rank_movement

    assert len(RANKS) == 7
    assert rank_movement(previous="learner", current="capable", evidence=("real test",))["arrow"] == "↑"
    assert rank_movement(previous="proven", current="proven")["arrow"] == "→"
    assert rank_movement(previous="expert", current="capable", evidence=("regression",))["arrow"] == "↓"


def test_rank_changes_require_evidence_and_never_grant_authority():
    from mission_control.agent_passports import rank_movement

    with pytest.raises(ValueError, match="rank_change_requires_evidence"):
        rank_movement(previous="learner", current="elite")
    with pytest.raises(ValueError, match="unknown_agent_rank"):
        rank_movement(previous="invented", current="elite", evidence=("claim",))
    result = rank_movement(previous="learner", current="capable", evidence=("verified",))
    assert result["execution_authorised"] is False
