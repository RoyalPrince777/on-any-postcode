from __future__ import annotations

import json

from mission_control import agents, config


def test_registry_locks_seven_oap_owned_families():
    assert agents.INTELLIGENCE_WORLD_NAMES == (
        "Civic Intelligence",
        "Jungle Book Intelligence",
        "Animal Intelligence",
        "Matrix Intelligence",
        "Civilisation Intelligence",
        "Akan Core Intelligence",
        "Akan Animal Intelligence",
    )
    assert len(agents.LOCKED_FAMILY_IDS) == 7
    assert len(set(agents.LOCKED_FAMILY_IDS)) == 7


def test_providers_are_separate_from_oap_agents_and_families():
    family_names = set(agents.INTELLIGENCE_WORLD_NAMES)
    agent_names = {agent["name"] for agent in agents.AGENT_REGISTRY}
    provider_names = {provider["name"] for provider in agents.INTELLIGENCE_PROVIDERS}

    assert provider_names == {
        "GPT",
        "Claude",
        "Gemini",
        "Kimi",
        "Grok",
        "Edge/Copilot",
        "Ollama Local",
    }
    assert family_names.isdisjoint(provider_names)
    assert agent_names.isdisjoint(provider_names)


def test_agent_registry_is_unique_safe_and_contains_confirmed_agents():
    validation = agents.validate_agent_registry()
    names = {agent["name"] for agent in agents.AGENT_REGISTRY}

    assert validation["passed"] is True
    assert validation["errors"] == []
    assert validation["checks"]["registered_agents"] == 25
    assert validation["checks"]["duplicate_agent_ids"] == 0
    assert validation["checks"]["duplicate_agent_names"] == 0
    assert validation["checks"]["duplicate_approved_roles"] == 0
    assert validation["checks"]["duplicate_providers"] == 0
    assert {"Neo", "Akela", "Bagheera", "Gyata", "Shere Khan"} <= names
    assert "Kaa" not in names


def test_neo_passport_preserves_locked_identity_and_authority():
    neo = next(agent for agent in agents.AGENT_REGISTRY if agent["agent_id"] == "NEO-001")

    assert neo["name"] == "Neo"
    assert neo["family_id"] == "matrix"
    assert neo["role"] == "Kernel Sentinel"
    assert neo["organ"] == "Brain"
    assert neo["powered_by"] == "ON ANY POSTCODE"
    assert neo["created_by"]["authority"] == "Human Authority"
    assert neo["identity"]["classification"] == "Intelligence Cell"
    assert neo["soul"]["purpose"] == "Solve complex problems"
    assert neo["mind"]["memory_access"] == "HRM Approved"
    assert neo["body"]["tools"] == ("analysis", "communication")
    assert neo["permissions"] == ("READ", "ANALYSE", "RECOMMEND")
    assert "Cannot override Human Authority" in neo["restrictions"]
    assert neo["guardian"] == "OAP Guardian"
    assert neo["supervisor"] == "Living Kernel"
    assert neo["audit_required"] is True
    assert neo["authority"]["level"] == 4
    assert neo["memory"] == {"system": "HRM Core", "audit": True}
    assert neo["status"] == "ACTIVE"


def test_unapproved_roles_and_provider_assignments_are_not_invented():
    pending_agents = [agent for agent in agents.AGENT_REGISTRY if agent["name"] != "Neo"]

    assert pending_agents
    assert all(agent["role"] is None for agent in pending_agents)
    assert all(agent["brain_region"] is None for agent in pending_agents)
    assert all(agent["powered_by"] == "ON ANY POSTCODE" for agent in agents.AGENT_REGISTRY)
    assert all(agent["provider_ids"] == () for agent in agents.AGENT_REGISTRY)
    assert all("EXECUTE" not in agent["permissions"] for agent in agents.AGENT_REGISTRY)


def test_duplicate_approved_role_is_rejected():
    duplicate_role = {
        **agents.AGENT_REGISTRY[1],
        "role": "Kernel Sentinel",
        "role_status": "Approved",
    }
    validation = agents.validate_agent_registry(
        agents=(agents.AGENT_REGISTRY[0], duplicate_role)
    )

    assert validation["passed"] is False
    assert any("Duplicate approved agent roles" in error for error in validation["errors"])


def test_agent_ui_is_read_only_and_does_not_create_database(
    client, tmp_path, monkeypatch
):
    database_path = tmp_path / "agent-intelligence.db"
    monkeypatch.setattr(config, "OAP_DATABASE_PATH", str(database_path))

    response = client.get("/mission/agents")
    page = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Your OAP Agents" in page
    assert "Seven owned worlds" in page
    assert "Neo" in page
    assert "Akela" in page
    assert "Gyata" in page
    assert "Providers are not agents" not in page
    assert "Powered by providers" in page
    assert 'method="get"' in page
    assert 'method="post"' not in page.lower()
    assert "Operational controls unavailable" in page
    assert client.post("/mission/agents").status_code == 405
    assert not database_path.exists()


def test_family_filter_and_empty_roster_are_honest(client):
    matrix = client.get("/mission/agents?family=matrix").get_data(as_text=True)
    civic = client.get("/mission/agents?family=civic").get_data(as_text=True)

    assert "Neo" in matrix
    assert "Morpheus" in matrix
    assert 'id="agent-jungle-akela-001"' not in matrix
    assert "No confirmed agents match this filter" in civic
    assert 'aria-current="page"' in matrix


def test_invalid_family_fails_closed(client):
    response = client.get("/mission/agents?family=providers")

    assert response.status_code == 400
    payload = response.get_json()
    assert payload["error"]["code"] == "invalid_intelligence_family"
    assert payload["error"]["allowed_families"] == list(agents.LOCKED_FAMILY_IDS)


def test_search_is_filtered_and_escaped(client):
    neo = client.get("/mission/agents?q=neo").get_data(as_text=True)
    attack = '<script>alert("agent")</script>'
    escaped = client.get("/mission/agents", query_string={"q": attack})
    escaped_page = escaped.get_data(as_text=True)

    assert "Neo" in neo
    assert 'id="agent-jungle-akela-001"' not in neo
    assert attack not in escaped_page
    assert "&lt;script&gt;" in escaped_page


def test_public_directory_excludes_secrets_and_legacy_terminology():
    serialized = json.dumps(agents.get_public_agent_directory()).lower()

    for private_key in ("secret", "token", "password", "totp", "correlation_id"):
        assert private_key not in serialized
    assert "council" not in serialized
    assert '"kaa"' not in serialized
