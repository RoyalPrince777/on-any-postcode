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
