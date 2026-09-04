from mission_control import smi_capabilities, technology_intelligence
from oap.smi.agi_core import AGICore


def test_6g_connectivity_routes_to_technology_and_matrix():
    route = AGICore().route(
        "Plan a local-first 6G edge AI and eSIM connectivity architecture.",
        "TECHNICAL",
    )
    assert "technology" in route["domain_ids"]
    assert "matrix" in route["domain_ids"]
    assert "6g" in route["matches"]["technology"]
    assert route["decision_authority"] is False
    assert route["execution_authority"] is False
    assert route["human_authority_final"] is True


def test_technology_registry_keeps_6g_nested_and_non_executing():
    status = technology_intelligence.technology_intelligence_status()
    smi = smi_capabilities.smi_capability_status()
    assert status["name"] == "Technology Intelligence"
    assert status["connectivity"]["name"] == "Connectivity Intelligence"
    assert status["connectivity"]["6g"]["name"] == "6G Intelligence"
    assert status["6g_architecture_ready"] is True
    assert status["6g_production_network_ready"] is False
    assert status["intelligence_world_count_added"] == 0
    assert status["network_execution_authority"] is False
    assert smi["validation"]["checks"]["intelligence_worlds"] == 7
    assert smi["specialist_status"]["technology"] == status
