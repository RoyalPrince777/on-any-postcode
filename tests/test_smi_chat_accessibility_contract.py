from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_chat_surface_exposes_live_and_control_labels():
    base = (ROOT / "mission_control/templates/ollama_chat_base.html").read_text()
    assert 'aria-live="polite"' in base
    assert 'aria-label="Voice input"' in base
    assert 'aria-label="Stop response"' in base
    assert 'aria-label="Send"' in base
    assert 'aria-label="Add attachment"' in base


def test_capture_controls_receive_accessible_labels():
    controller = (ROOT / "mission_control/static/smi_canonical_controller.js").read_text()
    assert "Capture camera image" in controller
    assert "Share screen and capture frame" in controller
