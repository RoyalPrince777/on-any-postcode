from pathlib import Path


def test_map_intelligence_contract_has_one_tool_family():
    text = Path("mission_control/templates/map_intelligence_contract.html").read_text(encoding="utf-8")
    assert "Map Intelligence" in text
    for tool in ("Map", "Routes", "Weather", "Travel", "Movement", "OAP Direct", "Delivery"):
        assert tool in text
    assert "movement-delivery" not in text


def test_map_intelligence_truth_lock_is_visible():
    text = Path("mission_control/templates/map_intelligence_contract.html").read_text(encoding="utf-8").casefold()
    for term in ("booking", "payment", "dispatch", "live tracking", "proof gates"):
        assert term in text
