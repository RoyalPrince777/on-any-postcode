"""Real Flask contract tests for the opt-in Founder-only still-image Vision route."""
import base64
from io import BytesIO

import pytest
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
    monkeypatch.setattr(studio_face_detection, "detect_faces_bounded", unavailable)
    result = _send(client, csrf["csrf_token"])
    assert result.status_code == 503
    assert result.json["error"]["code"] == "face_detector_unavailable"


def test_rate_limit_fails_closed(client, csrf, monkeypatch):
    monkeypatch.setenv("OAP_SMI_FACE_DETECTION_ENABLED", "true")
    monkeypatch.setattr(views, "_vision_face_rate_allowed", lambda _: False)
    result = _send(client, csrf["csrf_token"])
    assert result.status_code == 429
    assert result.json["error"]["code"] == "rate_limited"


def test_face_detector_has_separate_seven_per_minute_cpu_budget(client, csrf, monkeypatch):
    """Seven permitted attempts; chat's larger coalescing limiter stays untouched."""
    monkeypatch.setenv("OAP_SMI_FACE_DETECTION_ENABLED", "true")
    monkeypatch.setattr(
        studio_face_detection,
        "detect_faces_bounded",
        lambda image: {"state": "analysed", "face_count": 0, "faces": [],
                       "identity_verified": False},
    )
    limiter = web_security.VISION_FACE_BURST_LIMITER
    assert limiter.limit == 7
    assert limiter.window_seconds == 60
    assert limiter.fingerprint_request_body is False
    before = dict(web_security.CHAT_BURST_LIMITER._events)
    for _ in range(7):
        assert _send(client, csrf["csrf_token"]).status_code == 200
    eighth = _send(client, csrf["csrf_token"])
    assert eighth.status_code == 429
    assert eighth.json["error"]["code"] == "rate_limited"
    assert dict(web_security.CHAT_BURST_LIMITER._events) == before


def test_face_route_never_exports_even_route_metadata_to_external_telemetry(
    client, csrf, monkeypatch,
):
    """Ordinary local HTTP logging persists, but external telemetry excludes this path."""
    import app as app_module

    emitted = []
    monkeypatch.setattr(
        app_module.telemetry,
        "record_http_request",
        lambda **kwargs: emitted.append(kwargs),
    )
    monkeypatch.delenv("OAP_SMI_FACE_DETECTION_ENABLED", raising=False)
    response = _send(client, csrf["csrf_token"])
    assert response.status_code == 423
    assert emitted == []
    client.get("/healthz")
    assert emitted
    assert all("/mission/studio/vision/faces" not in str(row) for row in emitted)


def test_parallel_face_work_fails_fast_without_running_detector(client, csrf, monkeypatch):
    """Another expensive frame must get 503, not queue in worker memory."""
    monkeypatch.setenv("OAP_SMI_FACE_DETECTION_ENABLED", "true")
    def cannot_decode(image_data):
        raise AssertionError("The occupied detector must not decode another image")
    monkeypatch.setattr(studio_face_detection, "detect_faces_bounded", cannot_decode)
    slot = studio_face_detection.SINGLE_FRAME_PROCESS_SLOT
    assert slot.acquire(blocking=False)
    try:
        response = _send(client, csrf["csrf_token"])
        assert response.status_code == 503
        assert response.json["error"]["code"] == "face_detector_busy"
        assert response.headers["Cache-Control"] == "no-store"
        assert response.headers["X-Content-Type-Options"] == "nosniff"
    finally:
        slot.release()


def test_face_processing_slot_released_after_success_or_bad_frame(
    client, csrf, monkeypatch,
):
    """No persistent lockout after normal completion or malformed image."""
    monkeypatch.setenv("OAP_SMI_FACE_DETECTION_ENABLED", "true")
    slot = studio_face_detection.SINGLE_FRAME_PROCESS_SLOT
    assert _send(client, csrf["csrf_token"]).status_code == 200
    assert slot.acquire(blocking=False)
    slot.release()
    bad = _send(client, csrf["csrf_token"], {"image_data": {"invalid": True}})
    assert bad.status_code == 400
    assert slot.acquire(blocking=False)
    slot.release()


def test_face_processing_slot_released_after_unavailable_detector(
    client, csrf, monkeypatch,
):
    """Local detector failure must not deadlock later user attempts."""
    monkeypatch.setenv("OAP_SMI_FACE_DETECTION_ENABLED", "true")
    def unavailable(image_data):
        raise RuntimeError("face_detector_unavailable")
    monkeypatch.setattr(studio_face_detection, "detect_faces_bounded", unavailable)
    result = _send(client, csrf["csrf_token"])
    assert result.status_code == 503
    assert result.json["error"]["code"] == "face_detector_unavailable"
    slot = studio_face_detection.SINGLE_FRAME_PROCESS_SLOT
    assert slot.acquire(blocking=False)
    slot.release()


class _SharedAdmissionResult:
    def __init__(self, admitted):
        self.admitted = admitted

    def fetchone(self):
        return (self.admitted,)


class _SharedAdmissionConnection:
    def __init__(self, admitted):
        self.admitted = admitted
        self.closed = False
        self.queries = []

    def __enter__(self):
        return self

    def __exit__(self, *_exc):
        self.closed = True

    def execute(self, statement, parameters=None):
        self.queries.append((statement, parameters))
        return _SharedAdmissionResult(self.admitted)


def test_shared_admission_rejects_other_workers_before_image_parsing(
    client, csrf, monkeypatch,
):
    """An occupied OAP-owned database advisory slot must fail closed."""
    monkeypatch.setenv("OAP_SMI_FACE_DETECTION_ENABLED", "true")
    monkeypatch.setenv("OAP_SMI_FACE_SHARED_GUARD_REQUIRED", "true")
    monkeypatch.setattr(views.studio_face_admission, "reserve_shared_quota", lambda _: True)
    connection = _SharedAdmissionConnection(admitted=False)
    monkeypatch.setattr(views.postgres_db, "connect", lambda: connection)

    def must_not_decode(_image_data):
        raise AssertionError("Busy shared admission must never decode")

    monkeypatch.setattr(studio_face_detection, "detect_faces_bounded", must_not_decode)
    response = _send(client, csrf["csrf_token"])
    assert response.status_code == 503
    assert response.json["error"]["code"] == "face_detector_busy"
    assert connection.queries == [
        ("SET LOCAL statement_timeout = '1500ms'", None),
        ("SELECT pg_try_advisory_xact_lock(%s, %s)", (777, 1305))
    ]
    assert connection.closed is True
    assert response.headers["Cache-Control"] == "no-store"
    slot = studio_face_detection.SINGLE_FRAME_PROCESS_SLOT
    assert slot.acquire(blocking=False)
    slot.release()


def test_shared_admission_connection_failure_blocks_vision(
    client, csrf, monkeypatch,
):
    """Database outage must never fall back to process-local-only approval."""
    monkeypatch.setenv("OAP_SMI_FACE_DETECTION_ENABLED", "true")
    monkeypatch.setenv("OAP_SMI_FACE_SHARED_GUARD_REQUIRED", "true")

    monkeypatch.setattr(views.studio_face_admission, "reserve_shared_quota", lambda _: True)

    def unavailable():
        raise RuntimeError("private-database-unavailable")

    monkeypatch.setattr(views.postgres_db, "connect", unavailable)
    response = _send(client, csrf["csrf_token"])
    assert response.status_code == 503
    assert response.json["error"]["code"] == "face_shared_guard_unavailable"
    assert "private-database" not in response.get_data(as_text=True)
    slot = studio_face_detection.SINGLE_FRAME_PROCESS_SLOT
    assert slot.acquire(blocking=False)
    slot.release()


def test_shared_admission_held_through_decode_then_released(
    client, csrf, monkeypatch,
):
    """Owned database transaction must surround the complete detector operation."""
    monkeypatch.setenv("OAP_SMI_FACE_DETECTION_ENABLED", "true")
    monkeypatch.setenv("OAP_SMI_FACE_SHARED_GUARD_REQUIRED", "true")
    monkeypatch.setattr(views.studio_face_admission, "reserve_shared_quota", lambda _: True)
    connection = _SharedAdmissionConnection(admitted=True)
    monkeypatch.setattr(views.postgres_db, "connect", lambda: connection)

    def checked_detector(_image_data):
        assert connection.closed is False
        assert connection.queries == [
            ("SET LOCAL statement_timeout = '1500ms'", None),
            ("SELECT pg_try_advisory_xact_lock(%s, %s)", (777, 1305))
        ]
        return {"state": "analysed", "face_count": 0, "faces": [],
                "identity_verified": False}

    monkeypatch.setattr(studio_face_detection, "detect_faces_bounded", checked_detector)
    response = _send(client, csrf["csrf_token"])
    assert response.status_code == 200
    assert connection.closed is True
    slot = studio_face_detection.SINGLE_FRAME_PROCESS_SLOT
    assert slot.acquire(blocking=False)
    slot.release()


@pytest.mark.parametrize("failure", ["exhausted", "database"])
def test_shared_quota_blocks_before_detector(client, csrf, monkeypatch, failure):
    monkeypatch.setenv("OAP_SMI_FACE_DETECTION_ENABLED", "true")
    monkeypatch.setenv("OAP_SMI_FACE_SHARED_GUARD_REQUIRED", "true")

    def reserve(_identity):
        if failure == "database":
            raise RuntimeError("private database details")
        return False

    def must_not_decode(_image):
        raise AssertionError("Quota rejection must precede image processing")

    monkeypatch.setattr(views.studio_face_admission, "reserve_shared_quota", reserve)
    monkeypatch.setattr(studio_face_detection, "detect_faces_bounded", must_not_decode)
    response = _send(client, csrf["csrf_token"])
    assert response.status_code == (429 if failure == "exhausted" else 503)
    assert response.headers["Cache-Control"] == "no-store"
    assert "private database" not in response.get_data(as_text=True)


def test_timeout_releases_admission_and_returns_safe_error(client, csrf, monkeypatch):
    monkeypatch.setenv("OAP_SMI_FACE_DETECTION_ENABLED", "true")

    def timeout(_image):
        raise RuntimeError("face_detector_timeout")

    monkeypatch.setattr(studio_face_detection, "detect_faces_bounded", timeout)
    response = _send(client, csrf["csrf_token"])
    assert response.status_code == 503
    assert response.json["error"]["code"] == "face_detector_timeout"
    slot = studio_face_detection.SINGLE_FRAME_PROCESS_SLOT
    assert slot.acquire(blocking=False)
    slot.release()
