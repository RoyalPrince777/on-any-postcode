import json
from pathlib import Path


def test_machine_readable_map_intelligence_contract():
    contract = json.loads(Path("mission_control/map_intelligence_contract.json").read_text(encoding="utf-8"))
    assert contract["name"] == "Map Intelligence"
    assert contract["canonical_public_slug"] == "maps-weather-travel"
    assert contract["retired_public_slugs"] == ["movement-delivery"]
    assert len(contract["tools"]) == len(set(contract["tools"]))
