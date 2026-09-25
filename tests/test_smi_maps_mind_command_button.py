"""Maps MIND reuses the canonical SMI Map Intelligence body/workspace."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMMAND = ROOT / "mission_control/static/smi_command_centre.js"
MASTER = ROOT / "mission_control/static/smi_chat_final.js"


def test_maps_mind_button_reuses_canonical_smi_action() -> None:
    command = COMMAND.read_text(encoding="utf-8")
    master = MASTER.read_text(encoding="utf-8")
    assert '["🗺️ Maps · Mind","map-intelligence"]' in command
    assert 'const canonical=document.querySelector(\'#attach-menu [data-oap-action="\'+action+\'"]\')' in command
    assert 'id==="map-intelligence"' in master
    assert 'openMapWorkspace("/on-any-place")' in master or "openMapWorkspace('/on-any-place')" in master


def test_maps_mind_command_does_not_create_second_map_runtime() -> None:
    command = COMMAND.read_text(encoding="utf-8")
    assert 'window.location.assign("/mission/map-intelligence")' not in command
    assert "navigator.geolocation" not in command
    assert "/map-intelligence/road-geometry/" not in command


def test_canonical_map_workspace_keeps_same_origin_map_body() -> None:
    master = MASTER.read_text(encoding="utf-8")
    assert "openMapWorkspace" in master
    assert "/on-any-place" in master
    assert "data-map-view" in master
