from mission_control import location_intelligence


def test_location_status_exposes_earth_intelligence_contract():
    status = location_intelligence.status()

    assert status["earth_intelligence_architecture_passed"] is True
    assert status["earth_intelligence_component_count"] == 8
    assert "earth_intelligence" in status
    assert status["earth_intelligence"]["the_spot_connected"] is True
    assert status["earth_intelligence"]["spatial_binding"] == "POSTCODE_TO_UNIVERSE"
