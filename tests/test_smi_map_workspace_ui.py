from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "mission_control" / "templates" / "ollama_chat_base.html"
FINAL = ROOT / "mission_control" / "static" / "smi_chat_final.js"


def test_map_intelligence_is_visible_in_master_tools():
    base = BASE.read_text(encoding="utf-8")
    assert 'data-oap-action="map-intelligence"' in base
    assert "Map Intelligence" in base
    assert 'id="smi-map-workspace"' in base
    assert 'id="smi-map-frame"' in base


def test_map_workspace_reuses_first_party_map_surface():
    base = BASE.read_text(encoding="utf-8")
    assert 'src="/on-any-place"' in base
    for route in (
        "/on-any-place",
        "/movement",
        "/travel/direct",
        "/map-intelligence/status",
    ):
        assert f'data-map-view="{route}"' in base
    assert 'target="_blank"' in base


def test_map_workspace_has_mobile_and_full_screen_ux():
    base = BASE.read_text(encoding="utf-8")
    assert "position:fixed;inset:0" in base
    assert "@media(max-width:760px)" in base
    assert "body.smi-map-open{overflow:hidden}" in base
    assert 'aria-label="Close Map Intelligence"' in base


def test_map_workspace_has_runtime_handlers():
    script = FINAL.read_text(encoding="utf-8")
    for marker in (
        "openMapWorkspace",
        "closeMapWorkspace",
        "mapIntelligenceWorkspace:true",
        "data-map-view",
        "Escape",
        "/on-any-place",
    ):
        assert marker in script
