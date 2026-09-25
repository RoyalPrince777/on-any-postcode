from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMMAND = ROOT / "mission_control/static/smi_command_centre.js"
INTERACTION = ROOT / "mission_control/static/smi_interaction_layer.js"


def test_command_centre_exposes_screen_intelligence_button() -> None:
    command = COMMAND.read_text(encoding="utf-8")
    assert '["🖥️ Screen Intelligence","screen-intelligence"]' in command
    assert 'action==="screen-intelligence"' in command
    assert 'document.getElementById("screen-menu-button")' in command
    assert "screen.click()" in command


def test_screen_button_reuses_existing_bounded_capture_owner() -> None:
    interaction = INTERACTION.read_text(encoding="utf-8")
    assert 'screen-menu-button' in interaction
    assert "getDisplayMedia({video: true, audio: false})" in interaction
    assert "applyVisionImage" in interaction
    assert "track.stop()" in interaction
