from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_capture_options_are_explicit_and_not_silent():
    text = (ROOT / "mission_control/static/smi_canonical_controller.js").read_text()
    assert "📷 Camera" in text
    assert "🖥️ Share Screen" in text
    assert "Camera permission required" in text
    assert "Choose a screen to share" in text
