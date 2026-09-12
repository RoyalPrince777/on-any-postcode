from mission_control.map_intelligence import map_intelligence_manifest
from mission_control.products import get_public_product_hierarchy


def test_map_intelligence_obeys_one_front_door_law():
    manifest = map_intelligence_manifest()
    hierarchy = get_public_product_hierarchy()
    assert manifest["law"] == hierarchy["law"]
    assert hierarchy["law"] == "One World. One Front Door. Many Systems Inside."
