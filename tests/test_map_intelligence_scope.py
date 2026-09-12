from mission_control.map_intelligence import MAP_INTELLIGENCE_TOOLS


def test_map_intelligence_scope_is_complete():
    assert MAP_INTELLIGENCE_TOOLS == (
        "Map", "Routes", "Weather", "Travel", "Movement", "OAP Direct", "Booking", "Delivery"
    )
