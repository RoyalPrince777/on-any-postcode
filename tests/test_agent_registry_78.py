from collections import Counter

from mission_control.agents import (
    AGENT_REGISTRY,
    INTELLIGENCE_FAMILIES,
    INTELLIGENCE_PROVIDERS,
    INTELLIGENCE_WORLDS,
    LOCKED_AGENT_COUNT,
    validate_agent_registry,
)

EXPECTED_FAMILY_COUNTS = {
    "civic": 19,
    "jungle_book": 10,
    "animal": 21,
    "matrix": 7,
    "civilisation": 7,
    "akan_core": 1,
    "akan_animal": 13,
}


def test_registry_contains_exactly_78_complete_oap_agents():
    assert LOCKED_AGENT_COUNT == 78
    assert len(AGENT_REGISTRY) == LOCKED_AGENT_COUNT
    assert Counter(agent["family_id"] for agent in AGENT_REGISTRY) == EXPECTED_FAMILY_COUNTS
    assert tuple(world["id"] for world in INTELLIGENCE_WORLDS) == (
        "earth",
        "language",
        "life",
        "movement",
        "civic",
        "civilisation",
        "matrix",
    )
    assert len(INTELLIGENCE_FAMILIES) == 7


def test_every_agent_has_a_complete_human_governed_passport():
    required = {
        "agent_id",
        "created_by",
        "version",
        "name",
        "family_id",
        "identity",
        "role",
        "soul",
        "mind",
        "body",
        "permissions",
        "restrictions",
        "guardian",
        "supervisor",
        "memory_system",
        "audit_required",
        "authority",
        "memory",
        "status",
    }
    family_ids = {family["id"] for family in INTELLIGENCE_FAMILIES}

    for agent in AGENT_REGISTRY:
        assert required <= agent.keys()
        assert agent["family_id"] in family_ids
        assert agent["role"]
        assert agent["role_status"] == "Approved"
        assert {"soul", "mind", "body"} <= agent.keys()
        assert agent["guardian"] == "OAP Guardian"
        assert agent["supervisor"] == "Living Kernel"
        assert agent["memory_system"] == "HRM Core"
        assert agent["audit_required"] is True
        assert "READ" in agent["permissions"]
        assert "ANALYSE" in agent["permissions"]
        assert "RECOMMEND" in agent["permissions"]
        assert "EXECUTE" not in agent["permissions"]
        assert "Cannot override Human Authority" in agent["restrictions"]
        assert agent["provider_ids"] == ()
        assert agent["mind"]["provider_assignment"] == "Not assigned"
        assert agent["autonomy"]["mode"] == "BOUNDED_ADVISORY"
        assert agent["autonomy"]["can_analyse"] is True
        assert agent["autonomy"]["can_collaborate"] is True
        assert agent["autonomy"]["can_recommend"] is True
        assert agent["autonomy"]["can_approve"] is False
        assert agent["autonomy"]["can_execute"] is False
        assert agent["autonomy"]["final_authority"] == "Human Authority"
        assert agent["task_types"]


def test_registry_has_no_duplicate_identity_role_or_responsibility():
    result = validate_agent_registry()

    assert result["passed"] is True
    assert result["registry_complete"] is True
    assert result["ready_for_activation"] is False
    assert result["checks"]["duplicate_agent_ids"] == 0
    assert result["checks"]["duplicate_agent_names"] == 0
    assert result["checks"]["duplicate_approved_roles"] == 0
    assert result["checks"]["missing_approved_roles"] == 0
    assert result["checks"]["duplicate_responsibilities"] == 0
    assert result["checks"]["unsafe_authority"] == 0
    assert result["checks"]["bounded_autonomous_agents"] == 78
    assert result["checks"]["proposed_passports"] == 0
    assert result["checks"]["human_approved_passports"] == 78
    assert result["checks"]["canonical_world_alignment"] is True
    assert result["checks"]["matrix_home_system_aligned"] is True
    assert result["checks"]["nirmata_creation_architect_aligned"] is True


def test_nirmata_is_the_civilisation_creation_architect():
    nirmata = next(agent for agent in AGENT_REGISTRY if agent["name"] == "Nirmata")

    assert nirmata["agent_id"] == "NIRMATA-001"
    assert nirmata["family_id"] == "civilisation"
    assert nirmata["role"] == "Creation Architect"
    assert nirmata["organ"] == "Brain"
    assert "DESIGN" in nirmata["permissions"]
    assert "DRAFT_BLUEPRINT" in nirmata["permissions"]
    assert nirmata["body"]["execution"] == "Disabled"
    assert "Builder handoff" in nirmata["mind"]["capabilities"]
    assert nirmata["memory"]["record_every_design"] is True
    assert nirmata["autonomy"]["can_execute"] is False


def test_kaa_is_excluded_and_external_providers_are_not_agents():
    names_and_aliases = {
        label.casefold()
        for agent in AGENT_REGISTRY
        for label in (agent["name"], *agent.get("aliases", ()))
    }
    provider_names = {provider["name"] for provider in INTELLIGENCE_PROVIDERS}
    agent_names = {agent["name"] for agent in AGENT_REGISTRY}

    assert "kaa" not in names_and_aliases
    assert provider_names.isdisjoint(agent_names)
