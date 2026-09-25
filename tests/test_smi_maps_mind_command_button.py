"""Maps MIND stays a private navigation-only SMI Command Centre control."""
from pathlib import Path

JS = Path(__file__).resolve().parents[1] / "mission_control/static/smi_command_centre.js"


def test_maps_mind_button_reuses_private_map_intelligence_surface() -> None:
    script = JS.read_text(encoding="utf-8")
    assert '["🗺️ Maps · Mind","map-intelligence"]' in script
    assert 'action==="map-intelligence"' in script
    assert 'window.location.assign("/mission/map-intelligence")' in script


def test_maps_mind_button_does_not_create_location_or_execution_path() -> None:
    script = JS.read_text(encoding="utf-8")
    start = script.index('if(action==="map-intelligence")')
    end = script.index("const canonical=document.querySelector", start)
    handler = script[start:end]
    assert "geolocation" not in handler
    assert "fetch(" not in handler
    assert "dispatch" in handler
    assert "book" in handler
    assert "pay" in handler
