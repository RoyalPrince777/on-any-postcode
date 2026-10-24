"""Fail-closed tests for canonical Hybrid Agents HQ room projections."""

import pytest

from mission_control import agents
from mission_control.agents_hq import room_context, room_directory


def test_all_agents_uses_canonical_registry_without_new_passports():
    directory = room_directory()
    room = directory["rooms"][0]
    assert room["id"] == "all_agents"
    assert room["agent_ids"] == tuple(
        str(agent["agent_id"]) for agent in agents.AGENT_REGISTRY
    )
    assert directory["agent_count"] == len(agents.AGENT_REGISTRY)


def test_individual_room_has_one_registered_member():
    agent = agents.AGENT_REGISTRY[0]
    context = room_context(f"agent:{agent['agent_id']}")
    assert context["members"] == (
        {"agent_id": str(agent["agent_id"]), "name": str(agent["name"])},
    )


def test_family_rooms_match_canonical_family_membership():
    directory = room_directory()
    for family in agents.INTELLIGENCE_FAMILIES:
        room = room_context(f"family:{family['id']}")["room"]
        expected = tuple(
            str(agent["agent_id"])
            for agent in agents.AGENT_REGISTRY
            if agent.get("family_id") == family["id"]
        )
        assert room["agent_ids"] == expected
    assert len(directory["rooms"]) == (
        1 + len(agents.AGENT_REGISTRY) + len(agents.INTELLIGENCE_FAMILIES)
    )


@pytest.mark.parametrize(
    "room_id",
    ["", "agent:Mouse-not-registered", "family:beetle", "guest:butterfly"],
)
def test_unregistered_rooms_rejected(room_id):
    with pytest.raises(ValueError, match="Room ID required|Unknown canonical room"):
        room_context(room_id)


def test_no_false_chat_or_authority_claims():
    directory = room_directory()
    assert directory["messages"] == ()
    assert directory["message_history_available"] is False
    assert directory["autonomous_agent_chat"] is False
    assert directory["permissions_changed"] is False
    assert directory["can_execute"] is False
    context = room_context("all_agents")
    assert context["actual_messages"] == ()
    assert context["agent_responses_generated"] is False
    assert context["founder_final"] is True
