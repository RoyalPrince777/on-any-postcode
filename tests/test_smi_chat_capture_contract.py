from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTROLLER = ROOT / "mission_control" / "static" / "smi_canonical_controller.js"


def test_capture_is_permission_bound_and_stops_tracks():
    text = CONTROLLER.read_text(encoding="utf-8")
    assert "getUserMedia" in text
    assert "getDisplayMedia" in text
    assert "NotAllowedError" in text
    assert "stream.getTracks().forEach(track=>track.stop())" in text


def test_capture_reuses_existing_image_contract_not_new_studio_engine():
    text = CONTROLLER.read_text(encoding="utf-8")
    assert "selectedImage=dataUrl" in text
    assert "image-preview" in text
    assert "studioDuplicate:false" in text
    assert "new Studio" not in text
