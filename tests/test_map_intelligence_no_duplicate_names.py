from mission_control.products import PUBLIC_SPOT_CAPABILITIES


def test_public_map_movement_product_is_not_duplicated():
    names = [item["name"] for item in PUBLIC_SPOT_CAPABILITIES]
    assert names.count("Map Intelligence") == 1
    assert "Movement & Delivery" not in names
    assert "Maps, Weather & Travel" not in names
