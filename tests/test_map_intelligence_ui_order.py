from mission_control.map_intelligence import MAP_INTELLIGENCE_TOOLS


def test_map_intelligence_ui_order_is_action_first():
    assert MAP_INTELLIGENCE_TOOLS[:4] == ("Map", "Routes", "Weather", "Travel")
    assert MAP_INTELLIGENCE_TOOLS[4:] == ("Movement", "OAP Direct", "Booking", "Delivery")
