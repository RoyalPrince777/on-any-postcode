"""Maps MIND reuses the canonical SMI Map Intelligence body/workspace."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMMAND = ROOT / "mission_control/static/smi_command_centre.js"
MASTER = ROOT / "mission_control/static/smi_chat_final.js"


def test_maps_mind_button_reuses_canonical_smi_action() -> None:
    command = COMMAND.read_text(encoding="utf-8")
    master = MASTER.read_text(encoding="utf-8")
    assert '["🗺️ Maps Controls","oap-maps-controls"]' in command
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


def test_map_close_unloads_hidden_runtime_for_privacy_and_stop() -> None:
    master = MASTER.read_text(encoding="utf-8")
    start = master.index("function closeMapWorkspace()")
    end = master.index("qa('[data-map-view]')", start)
    close = master[start:end]
    assert "mapWorkspace.hidden=true" in close
    assert "mapFrame.src='about:blank'" in close
    assert "Map Intelligence stopped" in close


def test_maps_command_centre_exposes_mind_body_soul_controls() -> None:
    command = COMMAND.read_text(encoding="utf-8")
    assert '["🗺️ Maps Controls","oap-maps-controls"]' in command
    assert 'mapsControls.setAttribute("aria-label","Maps Mind Body Soul controls")' in command
    assert '["🧠 Mind"' in command
    assert '["⚙️ Body"' in command
    assert '["💛 Soul"' in command
    assert '["📊 Status"' in command
    assert 'action==="oap-maps-controls"' in command


def test_maps_body_button_reuses_existing_canonical_map_action() -> None:
    command = COMMAND.read_text(encoding="utf-8")
    assert 'button.dataset.mapsReview==="body"' in command
    assert 'data-oap-action="map-intelligence"' in command
    assert "canonical.click()" in command
    assert "navigator.geolocation" not in command
