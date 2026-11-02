"""OAP TV Founder upload: private, bounded, rights-locked intake."""
import io
import uuid

import pytest

from mission_control import tv_founder_intake


def test_upload_requires_configured_private_storage(monkeypatch, tmp_path):
    monkeypatch.delenv("OAP_TV_PRIVATE_MEDIA_DIR", raising=False)
    with pytest.raises(RuntimeError, match="not_configured"):
        tv_founder_intake.intake(io.BytesIO(b"0000ftypTEST"), content_type="video/mp4", title="Film", owner_id=str(uuid.uuid4()))


def test_founder_intake_persists_private_candidate_only(monkeypatch, tmp_path):
    monkeypatch.setenv("OAP_TV_PRIVATE_MEDIA_DIR", str(tmp_path))
    media = b"\x00\x00\x00\x10ftypisom" + b"0" * 16
    receipt = tv_founder_intake.intake(io.BytesIO(media), content_type="video/mp4", title=" My film ", owner_id=str(uuid.uuid4()))
    assert receipt["title"] == "My film"
    assert receipt["private_intake"] is True
    assert receipt["published"] is False
    assert receipt["playback_enabled"] is False
    assert receipt["rights_verified"] is False
    assert (tmp_path / (receipt["candidate_id"] + ".mp4")).read_bytes() == media


def test_rejects_unrecognised_content_and_oversize(monkeypatch, tmp_path):
    monkeypatch.setenv("OAP_TV_PRIVATE_MEDIA_DIR", str(tmp_path))
    owner = str(uuid.uuid4())
    for content_type, media in (
        ("video/mp4", b"not-an-mp4"),
        ("video/webm", b"not-webm"),
        ("application/octet-stream", b"1234"),
        ("video/mp4", b"\x00\x00\x00\x10ftyp" + b"x" * tv_founder_intake.MAX_VIDEO_BYTES),
    ):
        with pytest.raises(ValueError):
            tv_founder_intake.intake(io.BytesIO(media), content_type=content_type, title="Film", owner_id=owner)
    assert list(tmp_path.iterdir()) == []


def test_anonymous_upload_denied(anonymous_client):
    res = anonymous_client.post("/mission/organs/entertainment/tv/founder-upload")
    assert res.status_code in (401, 403)
