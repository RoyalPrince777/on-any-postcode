"""Regression checks for the advisory-only MI specialist roster."""

from mission_control.mi_specialists import MI_SPECIALISTS, validate_mi_specialists
from mission_control.agents import AGENT_REGISTRY, LOCKED_AGENT_COUNT


def test_mi_roster_is_complete_and_fail_closed():
    assert validate_mi_specialists()
    assert len(MI_SPECIALISTS) == 14
    assert all(agent["execution"] == "disabled" and agent["provider"] is None
               and agent["tools"] == () and agent["authority"] == "none"
               for agent in MI_SPECIALISTS)


def test_mi_definitions_do_not_modify_canonical_roster():
    assert len(AGENT_REGISTRY) == LOCKED_AGENT_COUNT
    assert not {agent["id"] for agent in MI_SPECIALISTS}.intersection(
        {agent.get("agent_id") for agent in AGENT_REGISTRY}
    )
