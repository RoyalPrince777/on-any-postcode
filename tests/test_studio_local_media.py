"""Focused fail-closed tests for OAP-owned local media composition."""
from pathlib import Path

import pytest

from mission_control import studio_local_media as render


def test_duration_and_filename_guards(tmp_path):
    (tmp_path / "scene.png").write_bytes(b"image")
    with pytest.raises(ValueError, match="duration"):
        render.render_still_video(owner_directory=str(tmp_path), image_name="scene.png",
                                  output_name="clip.mp4", seconds=31)
    with pytest.raises(ValueError, match="filename"):
        render.render_still_video(owner_directory=str(tmp_path), image_name="../scene.png",
                                  output_name="clip.mp4")
    with pytest.raises(ValueError, match="filename"):
        render.render_still_video(owner_directory=str(tmp_path), image_name="scene.png",
                                  output_name="../clip.mp4")


def test_unavailable_renderer_fails_closed(tmp_path, monkeypatch):
    (tmp_path / "scene.png").write_bytes(b"image")
    monkeypatch.setattr(render.shutil, "which", lambda _: None)
    with pytest.raises(render.StudioRenderUnavailable, match="ffmpeg_unavailable"):
        render.render_still_video(owner_directory=str(tmp_path), image_name="scene.png",
                                  output_name="clip.mp4")
    assert not (tmp_path / "clip.mp4").exists()


def test_rejects_existing_output_and_symlink(tmp_path):
    (tmp_path / "scene.png").write_bytes(b"image")
    (tmp_path / "clip.mp4").write_bytes(b"existing")
    with pytest.raises(ValueError, match="already_exists"):
        render.render_still_video(owner_directory=str(tmp_path), image_name="scene.png",
                                  output_name="clip.mp4")
    (tmp_path / "link.png").symlink_to(tmp_path / "scene.png")
    with pytest.raises(ValueError, match="missing_or_unsupported"):
        render.render_still_video(owner_directory=str(tmp_path), image_name="link.png",
                                  output_name="fresh.mp4")


def test_render_produces_verified_mp4_without_publishing(tmp_path, monkeypatch):
    (tmp_path / "scene.png").write_bytes(b"image")
    class Result:
        returncode = 0
        stdout = '{"streams":[{"codec_type":"video","width":720,"height":1280}],"format":{"duration":"4.0"}}'
    def fake_run(args, **_kwargs):
        if args[0].endswith("ffprobe"):
            return Result()
        assert args[1:5] == ["-nostdin", "-hide_banner", "-loglevel", "error"]
        assert "-loop" in args and "-pix_fmt" in args
        Path(args[-1]).write_bytes(b"\x00\x00\x00\x18ftypisom" + b"test" * 32)
        return Result()
    monkeypatch.setattr(render.shutil, "which", lambda name: "/usr/bin/" + name)
    monkeypatch.setattr(render.subprocess, "run", fake_run)
    result = render.render_still_video(owner_directory=str(tmp_path),
                                      image_name="scene.png", output_name="scene.mp4")
    assert result["rendered"] is True
    assert result["published"] is False
    assert len(result["sha256"]) == 64
    assert (tmp_path / "scene.mp4").is_file()
    assert not list(tmp_path.glob(".*.mp4"))

def test_invalid_mp4_probe_never_creates_published_artifact(tmp_path, monkeypatch):
    (tmp_path / "scene.png").write_bytes(b"image")

    class BadResult:
        returncode = 0
        stdout = '{"streams":[],"format":{"duration":"4.0"}}'

    def fake_run(args, **_kwargs):
        if args[0].endswith("ffprobe"):
            return BadResult()
        Path(args[-1]).write_bytes(b"\x00\x00\x00\x18ftypisom" + b"test" * 32)
        return BadResult()

    monkeypatch.setattr(render.shutil, "which", lambda name: "/usr/bin/" + name)
    monkeypatch.setattr(render.subprocess, "run", fake_run)
    with pytest.raises(render.StudioRenderUnavailable, match="probe_invalid"):
        render.render_still_video(
            owner_directory=str(tmp_path), image_name="scene.png", output_name="scene.mp4",
        )
    assert not (tmp_path / "scene.mp4").exists()
    assert not list(tmp_path.glob(".*.mp4"))
