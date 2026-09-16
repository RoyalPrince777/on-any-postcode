from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_media_capture_only_starts_from_explicit_button_handlers():
    text = (ROOT / "mission_control/static/smi_canonical_controller.js").read_text()
    assert "camera.addEventListener('click',oapCamera)" in text
    assert "screen.addEventListener('click',oapScreen)" in text
    assert "Camera permission required" in text
    assert "Choose a screen to share" in text
