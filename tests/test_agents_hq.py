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



def test_hq_page_and_room_api_use_registered_read_only_membership(client):
    page = client.get("/mission/smi/agents-hq")
    assert page.status_code == 200
    assert page.headers["Cache-Control"] == "no-store"
    assert "SMI Agents HQ" in page.get_data(as_text=True)
    assert "No message history or autonomous agent chat" in page.get_data(as_text=True)

    directory_response = client.get("/mission/smi/agents-hq/rooms")
    assert directory_response.status_code == 200
    assert directory_response.headers["Cache-Control"] == "no-store"
    directory = directory_response.get_json()
    assert directory["scope"] == "founder_only"
    assert directory["can_execute"] is False
    assert directory["message_history_available"] is False

    agent_id = agents.AGENT_REGISTRY[0]["agent_id"]
    context_response = client.get(f"/mission/smi/agents-hq/rooms/agent:{agent_id}")
    assert context_response.status_code == 200
    assert context_response.headers["Cache-Control"] == "no-store"
    context = context_response.get_json()
    assert context["room"]["id"] == f"agent:{agent_id}"
    assert context["agent_responses_generated"] is False
    assert context["can_execute"] is False


def test_hq_http_unknown_rooms_and_mutations_fail_closed(client):
    unknown = client.get("/mission/smi/agents-hq/rooms/guest:unregistered")
    assert unknown.status_code == 404
    assert unknown.get_json()["error"] == "unknown_room"
    assert unknown.headers["Cache-Control"] == "no-store"

    for path in (
        "/mission/smi/agents-hq",
        "/mission/smi/agents-hq/rooms",
        "/mission/smi/agents-hq/rooms/all_agents",
    ):
        assert client.post(path, json={"message": "execute"}).status_code == 405


def test_hq_anonymous_access_rejected(anonymous_client):
    page = anonymous_client.get("/mission/smi/agents-hq")
    assert page.status_code in (302, 303)
    for path in (
        "/mission/smi/agents-hq/rooms",
        "/mission/smi/agents-hq/rooms/all_agents",
    ):
        response = anonymous_client.get(path)
        assert response.status_code == 401
        assert response.get_json()["error"]["code"] == "authentication_required"
        assert response.headers["Cache-Control"] == "no-store"


def test_hq_authenticated_non_founder_access_rejected(client, monkeypatch):
    from mission_control import web_security

    monkeypatch.setattr(web_security, "private_authority_allowed", lambda _user: False)
    for path in (
        "/mission/smi/agents-hq",
        "/mission/smi/agents-hq/rooms",
        "/mission/smi/agents-hq/rooms/all_agents",
    ):
        response = client.get(path)
        assert response.status_code == 403
        assert response.get_json()["error"]["code"] == "human_authority_required"
        assert response.headers["Cache-Control"] == "no-store"
