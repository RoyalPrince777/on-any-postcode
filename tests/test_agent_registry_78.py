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
    assert len(INTELLIGENCE_WORLDS) == 6
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
        assert agent["permissions"] == ("READ", "ANALYSE", "RECOMMEND")
        assert "EXECUTE" not in agent["permissions"]
        assert "Cannot override Human Authority" in agent["restrictions"]
        assert agent["provider_ids"] == ()
        assert agent["mind"]["provider_assignment"] == "Not assigned"


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
    assert result["checks"]["proposed_passports"] == 0
    assert result["checks"]["human_approved_passports"] == 78


def test_nirmata_occupies_the_existing_civilisation_artisan_slot():
    nirmata = next(agent for agent in AGENT_REGISTRY if agent["name"] == "Nirmata")

    assert nirmata["agent_id"] == "CIVILISATION-ARTISAN-001"
    assert nirmata["family_id"] == "civilisation"
    assert nirmata["role"] == "Creation Design Steward"
    assert "Civilisation Artisan" in nirmata["aliases"]
    assert nirmata["body"]["execution"] == "Disabled"
    assert "Builder handoff" in nirmata["mind"]["capabilities"]


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

