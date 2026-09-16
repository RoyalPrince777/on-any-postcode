from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_controller_distinguishes_success_stop_and_failure():
    text = (ROOT / "mission_control/static/smi_canonical_controller.js").read_text()
    assert "Ready · governed result recorded" in text
    assert "Response stopped by Human Authority" in text
    assert "Request not completed safely" in text


def test_capture_distinguishes_permission_and_unavailable_states():
    text = (ROOT / "mission_control/static/smi_canonical_controller.js").read_text()
    assert "Camera permission blocked" in text
    assert "Camera unavailable" in text
    assert "Screen sharing cancelled or blocked" in text
    assert "Screen sharing unavailable" in text
