"""Private Studio Face Detection contract; no webcam, network or person IDs."""
import base64
import importlib.util
from io import BytesIO
from pathlib import Path

import pytest
from PIL import Image

MODULE = Path(__file__).resolve().parents[1] / "mission_control" / "studio_face_detection.py"
spec = importlib.util.spec_from_file_location("studio_face_detection", MODULE)
vision = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vision)


def data_url(size=(160, 120), mime="image/png", format="PNG"):
    image = Image.new("RGB", size, (95, 126, 161))
    buffer = BytesIO()
    image.save(buffer, format=format)
    return f"data:{mime};base64," + base64.b64encode(buffer.getvalue()).decode("ascii")


def test_real_opencv_no_faces_and_no_identifying_data():
    result = vision.detect_faces(data_url())
    assert result["face_count"] == 0
    assert result["faces"] == []
    assert result["raw_content_retained"] is False
    assert result["identity_verified"] is False
    assert result["execution_granted"] is False
    assert "data:image" not in str(result)


def test_detector_boxes_and_count(monkeypatch):
    import cv2
    class Detector:
        def __init__(self, path):
            assert path.endswith("haarcascade_frontalface_default.xml")
        def empty(self):
            return False
        def detectMultiScale(self, gray, **kwargs):
            assert kwargs["minNeighbors"] == 5
            return [(5, 9, 30, 30), (45, 18, 35, 35)]
    monkeypatch.setattr(cv2, "CascadeClassifier", Detector)
    result = vision.detect_faces(data_url())
    assert result["face_count"] == 2
    assert result["faces"] == [
        {"x": 5, "y": 9, "width": 30, "height": 30},
        {"x": 45, "y": 18, "width": 35, "height": 35},
    ]
    assert result["continuous_video_proven"] is False


@pytest.mark.parametrize("image", [None, 7, "", "not-an-image", "data:image/png;base64,@@", "data:image/png;base64,", "data:text/plain;base64,Zm9v"])
def test_rejects_invalid_input(image):
    with pytest.raises((TypeError, ValueError)):
        vision.detect_faces(image)


def test_rejects_format_spoofing():
    with pytest.raises(ValueError, match="face_image_format_mismatch"):
        vision.detect_faces(data_url(mime="image/jpeg"))


def test_rejects_oversized_dimension_before_decoding(monkeypatch):
    import cv2
    def must_not_decode(*args, **kwargs):
        raise AssertionError("decode should never occur")
    monkeypatch.setattr(cv2, "imdecode", must_not_decode)
    with pytest.raises(ValueError, match="face_image_dimensions_exceeded"):
        vision.detect_faces(data_url(size=(4096, 4096)))


def test_rejects_oversized_request_before_base64_decode():
    image = "data:image/png;base64," + "A" * (vision.MAX_IMAGE_BYTES * 2)
    with pytest.raises(ValueError, match="face_image_too_large"):
        vision.detect_faces(image)


def test_cascade_missing_fails_closed(monkeypatch):
    import cv2
    class MissingDetector:
        def __init__(self, path):
            pass
        def empty(self):
            return True
    monkeypatch.setattr(cv2, "CascadeClassifier", MissingDetector)
    with pytest.raises(RuntimeError, match="face_detector_unavailable"):
        vision.detect_faces(data_url())


def test_malformed_data_rejected():
    payload = "data:image/png;base64," + base64.b64encode(b"fake png").decode("ascii")
    with pytest.raises(ValueError, match="invalid_face_image"):
        vision.detect_faces(payload)


def test_private_route_keeps_auth_csrf_rate_and_default_lock():
    views = (Path(__file__).resolve().parents[1] / "mission_control" / "views.py").read_text()
    segment = views.split('@bp.post("/studio/vision/faces")', 1)[1].split(
        '@bp.post("/studio/generate")', 1
    )[0]
    assert "@web_security.login_required(api=True, founder_only=True)" in segment
    assert "web_security.csrf_valid(request)" in segment
    assert 'environ.get("OAP_SMI_FACE_DETECTION_ENABLED", "false")' in segment
    assert "_vision_face_rate_allowed(_chat_identity())" in segment
    assert "request.content_length" in segment
    assert "studio_face_detection.detect_faces(payload.get(\"image_data\"))" in segment
    assert "face_detector_unavailable" in segment
    assert "return _no_store(make_response(jsonify(result)))" in segment
