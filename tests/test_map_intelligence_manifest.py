from mission_control.map_intelligence import map_intelligence_manifest


def test_map_intelligence_manifest_is_complete_and_bounded():
    manifest = map_intelligence_manifest()
    assert manifest["name"] == "Map Intelligence"
    assert manifest["slug"] == "maps-weather-travel"
    assert set(("Map", "Routes", "Weather", "Travel", "Movement", "OAP Direct", "Booking", "Delivery")).issubset(set(manifest["tools"]))
    assert "movement-delivery" in manifest["retired_public_slugs"]
    assert "payment" in manifest["truth_locks"]
    assert "automatic dispatch" in manifest["truth_locks"]
