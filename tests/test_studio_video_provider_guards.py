"""Fail-closed video provider boundaries in the existing SMI Studio backend."""

import pytest

from mission_control import studio_media_backend as backend


@pytest.mark.parametrize(
    "video_id",
    [
        "video_../../credentials", "video_test?raw=1", "video_bad/other",
        "video_bad%2Fother", "video_bad\\n", "video_", "test_video",
        "video_" + "x" * 129,
    ],
)
def test_provider_video_ids_reject_paths_and_unbounded_values(video_id, monkeypatch):
    monkeypatch.setattr(
        backend, "_json_call",
        lambda *_args, **_kwargs: pytest.fail("invalid video id reached provider"),
    )
    with pytest.raises(ValueError, match="studio_video_id_invalid"):
        backend.video_status(video_id)
    with pytest.raises(ValueError, match="studio_video_id_invalid"):
        backend.video_content(video_id)


def test_video_status_allows_bounded_provider_id(monkeypatch):
    monkeypatch.setattr(
        backend, "_json_call",
        lambda *_args, **_kwargs: {"status": "in_progress", "progress": 30},
    )
    state = backend.video_status("video_abc-123")
    assert state["id"] == "video_abc-123"
    assert state["artifact_proven"] is False


def test_create_video_rejects_provider_job_id_injection(monkeypatch):
    monkeypatch.setattr(
        backend, "_multipart_call",
        lambda *_args, **_kwargs: {"id": "video_../../secrets", "status": "queued"},
    )
    with pytest.raises(ValueError, match="studio_video_id_invalid"):
        backend.create_video("A South London scene")


def test_mp4_header_validation_does_not_claim_decoder_verification():
    # Container signature alone is a minimal check, not proof of a playable video.
    sample = (24).to_bytes(4, "big") + b"ftypisom" + b"000000000000"
    assert backend._mp4_container_valid(sample) is True
    assert backend._mp4_container_valid(b"<html>upstream error</html>") is False
    assert backend._mp4_container_valid(b"") is False
    assert backend._mp4_container_valid(b"\x00\x00\x00\x08ftyp") is False


def test_video_content_rejects_provider_error_body(monkeypatch):
    monkeypatch.setattr(backend, "_key", lambda: "fake-test-key")

    class Response:
        headers = {"Content-Type": "video/mp4"}

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self, _size):
            return b"<html>bad gateway</html>"

    monkeypatch.setattr(backend.urlrequest, "urlopen", lambda *_args, **_kwargs: Response())
    with pytest.raises(RuntimeError, match="studio_video_content_invalid"):
        backend.video_content("video_abc123")
