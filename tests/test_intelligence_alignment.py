from mission_control.agents import (
    AGENT_REGISTRY,
    INTELLIGENCE_FAMILIES,
    INTELLIGENCE_WORLDS,
    ORGANISM_NON_AGENT_SYSTEMS,
)


def test_locked_seven_worlds_are_canonical():
    assert tuple(world["name"] for world in INTELLIGENCE_WORLDS) == (
        "Earth Intelligence",
        "Language Intelligence",
        "Life Intelligence",
        "Movement Intelligence",
        "Civic Intelligence",
        "Civilisation Intelligence",
        "Matrix Intelligence",
    )


def test_specialist_families_are_not_misclassified_as_worlds():
    world_names = {world["name"] for world in INTELLIGENCE_WORLDS}

    assert "Jungle Book Intelligence" not in world_names
    assert "Animal Intelligence" not in world_names
    assert "Akan Intelligence" not in world_names

    homes = {family["id"]: family for family in INTELLIGENCE_FAMILIES}
    assert homes["jungle_book"]["world_id"] == "life"
    assert homes["animal"]["world_id"] == "life"
    assert homes["akan_core"]["world_id"] == "civilisation"
    assert homes["akan_animal"]["world_id"] == "civilisation"
    assert homes["akan_animal"]["cross_world_ids"] == ("life",)


def test_matrix_agents_live_in_matrix_system():
    matrix_family = next(family for family in INTELLIGENCE_FAMILIES if family["id"] == "matrix")
    matrix_agents = [agent for agent in AGENT_REGISTRY if agent["family_id"] == "matrix"]

    assert matrix_family["world_id"] == "matrix"
    assert matrix_family["home_system"] == "Matrix System"
    assert len(matrix_agents) == 7
    assert {agent["name"] for agent in matrix_agents} == {
        "Neo",
        "Morpheus",
        "Trinity",
        "Oracle",
        "Architect",
        "Keymaker",
        "Seraph",
    }


def test_organism_systems_are_never_counted_as_agents():
    system_names = {item["name"] for item in ORGANISM_NON_AGENT_SYSTEMS}
    agent_names = {agent["name"] for agent in AGENT_REGISTRY}

    assert system_names.isdisjoint(agent_names)
    assert {"OASIS", "NEXUS", "SMI", "Living Kernel", "HRM Core"} <= system_names
