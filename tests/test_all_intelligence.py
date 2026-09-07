from mission_control import all_intelligence
from oap.smi.agi_core import AGICore

CANONICAL_WORLD_IDS = (
    "earth",
    "language",
    "life",
    "movement",
    "civic",
    "civilisation",
    "matrix",
)


def test_all_intelligence_keeps_one_brain_and_exactly_seven_worlds():
    status = all_intelligence.status()

    assert status["brain"]["count"] == 1
    assert status["brain"]["single_brain"] is True
    assert status["world_count"] == 7
    assert status["world_ids"] == CANONICAL_WORLD_IDS
    assert status["architecture_green"] is True
    assert status["routing_green"] is True
    assert status["execution_granted"] is False
    assert status["approval_granted"] is False
    assert status["human_authority_final"] is True


def test_all_intelligence_preserves_78_agents_and_seven_specialist_families():
    status = all_intelligence.status()

    assert status["agent_count"] == 78
    assert status["agent_target"] == 78
    assert status["family_count"] == 7
    assert status["registry_green"] is True
    assert status["memory_governed"] is True

    placement = {family["id"]: family["world_id"] for family in status["families"]}
    assert placement["civic"] == "civic"
    assert placement["jungle_book"] == "life"
    assert placement["animal"] == "life"
    assert placement["matrix"] == "matrix"
    assert placement["civilisation"] == "civilisation"
    assert placement["akan_core"] == "civilisation"
    assert placement["akan_animal"] == "civilisation"


def test_agi_router_uses_seven_world_projection_with_nested_specialists():
    router = AGICore().status()
    assert router["world_count"] == 7
    assert router["world_ids"] == CANONICAL_WORLD_IDS
    assert router["canonical_world_model"] is True
    assert router["brain_count"] == 0

    route = AGICore().route(
        "Akela reviews a Ghana international humanitarian video route with 6G connectivity.",
        "GENERAL",
    )
    assert set(route["world_ids"]) <= set(CANONICAL_WORLD_IDS)
    assert "jungle_book" in route["specialist_ids"]
    assert "akan" in route["specialist_ids"]
    assert "international_humanitarian" in route["specialist_ids"]
    assert "technology" in route["specialist_ids"]
    assert "multimodal" in route["specialist_ids"]
    assert "life" in route["world_ids"]
    assert "civilisation" in route["world_ids"]
    assert "matrix" in route["world_ids"]
    assert route["decision_authority"] is False
    assert route["execution_authority"] is False


def test_specialist_capabilities_do_not_expand_world_count():
    status = all_intelligence.status()
    cross_ids = tuple(item["id"] for item in status["cross_system_capabilities"])

    assert cross_ids == ("technology", "international_humanitarian", "multimodal")
    assert status["world_count"] == 7
    assert status["specialist_families_are_extra_worlds"] is False
    assert status["providers_are_agents"] is False


def test_all_intelligence_founder_page_is_read_only(client):
    response = client.get("/mission/intelligence")
    page = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "All Intelligence" in page
    assert "Seven Intelligence Worlds" in page
    assert "78/78 Agents" in page
    assert "Human Authority final" in page
    assert "Enable A7" not in page
