from mission_control.products import PUBLIC_SPOT_CAPABILITIES


def test_map_intelligence_is_only_named_map_movement_public_surface():
    competing = {"Maps, Weather & Travel", "Movement & Delivery"}
    names = {item["name"] for item in PUBLIC_SPOT_CAPABILITIES}
    assert "Map Intelligence" in names
    assert names.isdisjoint(competing)
