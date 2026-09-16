from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_camera_and_screen_capture_are_bounded_and_tracks_stop():
    text = (ROOT / "mission_control/static/smi_canonical_controller.js").read_text()
    assert "getUserMedia" in text
    assert "getDisplayMedia" in text
    assert "capturing one governed frame" in text
    assert "stream.getTracks().forEach(track=>track.stop())" in text


def test_capture_routes_through_existing_studio_path():
    text = (ROOT / "mission_control/static/smi_canonical_controller.js").read_text()
    assert "routed through existing image/Studio path" in text
    assert "studioDuplicate:false" in text
