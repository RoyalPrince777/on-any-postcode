from __future__ import annotations

import json

from mission_control import agents, config


def test_registry_locks_seven_worlds_and_seven_oap_owned_families():
    assert agents.INTELLIGENCE_WORLD_NAMES == (
        "Earth Intelligence",
        "Language Intelligence",
        "Life Intelligence",
        "Movement Intelligence",
        "Civic Intelligence",
        "Civilisation Intelligence",
        "Matrix Intelligence",
    )
    assert agents.INTELLIGENCE_FAMILY_NAMES == (
        "Civic Intelligence",
        "Jungle Book Intelligence",
        "Animal Intelligence",
        "Matrix Intelligence",
        "Civilisation Intelligence",
        "Akan Core Intelligence",
        "Akan Animal Intelligence",
    )
    assert len(agents.LOCKED_WORLD_IDS) == 7
    assert set(agents.LOCKED_WORLD_IDS) == {
        "earth",
        "language",
        "life",
        "movement",
        "civic",
        "civilisation",
        "matrix",
    }
    assert len(agents.LOCKED_FAMILY_IDS) == 7
    assert len(set(agents.LOCKED_FAMILY_IDS)) == 7

    families = {family["id"]: family for family in agents.INTELLIGENCE_FAMILIES}
    assert families["jungle_book"]["world_id"] == "life"
    assert families["animal"]["world_id"] == "life"
    assert families["matrix"]["world_id"] == "matrix"
    assert families["matrix"]["home_system"] == "Matrix System"
    assert families["akan_core"]["world_id"] == "civilisation"
    assert families["akan_animal"]["world_id"] == "civilisation"
    assert families["akan_animal"]["cross_world_ids"] == ("life",)


def test_providers_are_separate_from_oap_agents_and_families():
    family_names = set(agents.INTELLIGENCE_FAMILY_NAMES)
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
    assert validation["ready_for_activation"] is False
    assert validation["errors"] == []
    assert validation["checks"]["registered_agents"] == 78
    assert validation["checks"]["locked_agent_count"] == 78
    assert validation["checks"]["missing_passports"] == 0
    assert validation["checks"]["roster_complete"] is True
    assert validation["registry_complete"] is True
    assert validation["checks"]["proposed_passports"] == 0
    assert validation["checks"]["human_approved_passports"] == 78
    assert validation["checks"]["duplicate_agent_ids"] == 0
    assert validation["checks"]["duplicate_agent_names"] == 0
    assert validation["checks"]["duplicate_approved_roles"] == 0
    assert validation["checks"]["duplicate_providers"] == 0
    assert validation["checks"]["canonical_world_alignment"] is True
    assert validation["checks"]["matrix_home_system_aligned"] is True
    assert validation["checks"]["nirmata_creation_architect_aligned"] is True
    assert {"Neo", "Akela", "Bagheera", "Gyata", "Shere Khan", "Nirmata"} <= names
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


def test_nirmata_passport_is_canonical_and_non_executing():
    nirmata = next(agent for agent in agents.AGENT_REGISTRY if agent["name"] == "Nirmata")

    assert nirmata["agent_id"] == "NIRMATA-001"
    assert nirmata["family_id"] == "civilisation"
    assert nirmata["role"] == "Creation Architect"
    assert nirmata["organ"] == "Brain"
    assert nirmata["brain_region"].startswith("Civilisation Intelligence")
    assert nirmata["permissions"] == (
        "READ",
        "ANALYSE",
        "DESIGN",
        "RECOMMEND",
        "DRAFT_BLUEPRINT",
    )
    assert nirmata["body"]["execution"] == "Disabled"
    assert nirmata["memory"]["record_every_design"] is True
    assert nirmata["autonomy"]["can_execute"] is False


def test_approved_roles_are_complete_without_provider_assignments():
    approved_agents = [agent for agent in agents.AGENT_REGISTRY if agent["name"] != "Neo"]
    standard_agents = [agent for agent in approved_agents if agent["name"] != "Nirmata"]

    assert approved_agents
    assert all(agent["role"] for agent in approved_agents)
    assert all(agent["role_status"] == "Approved" for agent in approved_agents)
    assert all(agent["brain_region"] == "SMI advisory interface" for agent in standard_agents)
    assert all(agent["powered_by"] == "ON ANY POSTCODE" for agent in agents.AGENT_REGISTRY)
    assert all(agent["provider_ids"] == () for agent in agents.AGENT_REGISTRY)
    assert all("EXECUTE" not in agent["permissions"] for agent in agents.AGENT_REGISTRY)
    assert all(
        agent["autonomy"]["mode"] == "BOUNDED_ADVISORY"
        and agent["autonomy"]["can_execute"] is False
        for agent in agents.AGENT_REGISTRY
    )


def test_all_78_approved_passports_remain_runtime_disabled():
    assert len(agents.AGENT_REGISTRY) == 78
    assert all(agent["role_status"] == "Approved" for agent in agents.AGENT_REGISTRY)
    assert all(agent["provider_ids"] == () for agent in agents.AGENT_REGISTRY)
    assert all(
        agent["body"]["execution"] in {"Disabled", "Human approval required"}
        for agent in agents.AGENT_REGISTRY
    )
    assert all("EXECUTE" not in agent["permissions"] for agent in agents.AGENT_REGISTRY)


def test_approved_passport_cannot_gain_runtime_authority_by_field_mutation():
    original = next(
        agent for agent in agents.AGENT_REGISTRY if agent["name"] not in {"Neo", "Nirmata"}
    )
    unsafe = {
        **original,
        "status": "ACTIVE",
        "runtime_status": "Connected",
        "provider_ids": ("gpt",),
        "permissions": (*original["permissions"], "EXECUTE"),
        "body": {
            **original["body"],
            "tools": ("shell",),
            "actions": ("execute",),
            "execution": "Enabled",
        },
    }
    registry = tuple(
        unsafe if agent["agent_id"] == original["agent_id"] else agent
        for agent in agents.AGENT_REGISTRY
    )
    validation = agents.validate_agent_registry(agents=registry)

    assert validation["passed"] is False
    assert validation["ready_for_activation"] is False
    assert validation["checks"]["unsafe_authority"] == 1
    assert any("Unsafe agent authority" in error for error in validation["errors"])


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
    assert "Seven worlds · seven families" in page
    assert "Earth Intelligence is approved" in page
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


def test_family_filter_reports_approved_roster_honestly(client):
    matrix = client.get("/mission/agents?family=matrix").get_data(as_text=True)
    civic = client.get("/mission/agents?family=civic").get_data(as_text=True)

    assert "Neo" in matrix
    assert "Morpheus" in matrix
    assert 'id="agent-jungle-akela-001"' not in matrix
    assert "Postcode Beacon" in civic
    assert "ACTIVE" in civic
    assert "Bounded autonomous advisory — execution disabled" in civic
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
