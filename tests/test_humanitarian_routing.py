from oap.smi.agi_core import AGICore


def test_humanitarian_emergency_request_routes_to_technology_and_matrix():
    route = AGICore().route(
        "Prepare humanitarian emergency communications with SOS, family reunification and fallback connectivity.",
        "GENERAL",
    )

    assert "technology" in route["domain_ids"]
    assert "matrix" in route["domain_ids"]
    assert "humanitarian" in route["matches"]["technology"]
    assert route["decision_authority"] is False
    assert route["execution_authority"] is False
    assert route["human_authority_final"] is True


def test_humanitarian_map_request_routes_to_movement_earth_technology_and_matrix():
    route = AGICore().route(
        "Prepare a humanitarian map and safe route for civilians with connectivity fallback.",
        "GENERAL",
    )

    assert "movement" in route["domain_ids"]
    assert "earth" in route["domain_ids"]
    assert "technology" in route["domain_ids"]
    assert "matrix" in route["domain_ids"]
    assert "map" in route["matches"]["movement"]
    assert "humanitarian" in route["matches"]["technology"]
    assert route["decision_authority"] is False
    assert route["execution_authority"] is False
    assert route["human_authority_final"] is True
