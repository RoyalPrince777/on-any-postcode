"""Real Flask contract tests for the opt-in Founder-only still-image Vision route."""
import base64
from io import BytesIO

from PIL import Image

from mission_control import studio_face_detection, views, web_security

PATH = "/mission/studio/vision/faces"


def _image():
    buffer = BytesIO()
    Image.new("RGB", (160, 120), (80, 120, 170)).save(buffer, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode("ascii")


def _send(client, token, data=None):
    return client.post(
        PATH,
        json={"image_data": _image()} if data is None else data,
        headers={"X-OAP-CSRF": token},
    )


def test_anonymous_cannot_access_even_with_feature_enabled(anonymous_client, monkeypatch):
    monkeypatch.setenv("OAP_SMI_FACE_DETECTION_ENABLED", "true")
    result = _send(anonymous_client, "unused")
    assert result.status_code == 401
    assert result.json["error"]["code"] == "authentication_required"


def test_non_founder_blocked_even_when_enabled(client, csrf, monkeypatch):
    monkeypatch.setenv("OAP_SMI_FACE_DETECTION_ENABLED", "true")
    monkeypatch.setattr(web_security, "private_authority_allowed", lambda _: False)
    result = _send(client, csrf["csrf_token"])
    assert result.status_code == 403
    assert result.json["error"]["code"] == "human_authority_required"


def test_founder_route_is_locked_by_default(client, csrf, monkeypatch):
    monkeypatch.delenv("OAP_SMI_FACE_DETECTION_ENABLED", raising=False)
    result = _send(client, csrf["csrf_token"])
    assert result.status_code == 423
    assert result.json["error"]["code"] == "face_detection_locked"
    assert result.headers["Cache-Control"] == "no-store"


def test_csrf_is_required_even_when_disabled(client):
    result = _send(client, "bad-csrf-token")
    assert result.status_code == 403
    assert result.json["error"]["code"] == "csrf_failed"


def test_enabled_route_returns_boxes_without_identity_or_media(client, csrf, monkeypatch):
    monkeypatch.setenv("OAP_SMI_FACE_DETECTION_ENABLED", "true")
    result = _send(client, csrf["csrf_token"])
    assert result.status_code == 200
    assert result.json["face_count"] == 0
    assert result.json["image"] == {"width": 160, "height": 120}
    assert result.json["identity_verified"] is False
    assert result.json["raw_content_retained"] is False
    assert result.json["execution_granted"] is False
    assert "base64" not in result.get_data(as_text=True)
    assert result.headers["Cache-Control"] == "no-store"
    assert result.headers["X-Content-Type-Options"] == "nosniff"


def test_invalid_image_does_not_leak_raw_bytes(client, csrf, monkeypatch):
    monkeypatch.setenv("OAP_SMI_FACE_DETECTION_ENABLED", "true")
    result = _send(client, csrf["csrf_token"], {"image_data": {"bad": "data"}})
    assert result.status_code == 400
    assert result.json["error"]["code"] == "invalid_face_image"
    assert "data" not in result.get_data(as_text=True)


def test_unavailable_detector_fails_closed(client, csrf, monkeypatch):
    monkeypatch.setenv("OAP_SMI_FACE_DETECTION_ENABLED", "true")
    def unavailable(image_data):
        raise RuntimeError("face_detector_unavailable")
    monkeypatch.setattr(studio_face_detection, "detect_faces", unavailable)
    result = _send(client, csrf["csrf_token"])
    assert result.status_code == 503
    assert result.json["error"]["code"] == "face_detector_unavailable"


def test_rate_limit_fails_closed(client, csrf, monkeypatch):
    monkeypatch.setenv("OAP_SMI_FACE_DETECTION_ENABLED", "true")
    monkeypatch.setattr(views, "_vision_face_rate_allowed", lambda _: False)
    result = _send(client, csrf["csrf_token"])
    assert result.status_code == 429
    assert result.json["error"]["code"] == "rate_limited"
