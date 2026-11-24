"""Local media-preparation boundaries; no production worker required."""
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from mission_control import studio_video_tools


def test_probe_rejects_source_outside_owner_root(tmp_path):
    root = tmp_path / "owner"
    root.mkdir()
    outside = tmp_path / "outside.mp4"
    outside.write_bytes(b"some data")
    with pytest.raises(ValueError, match="unowned_path"):
        studio_video_tools.probe_owned_video(root=root, source=outside)


def test_probe_reads_metadata_without_provider(monkeypatch, tmp_path):
    src = tmp_path / "clip.mp4"
    src.write_bytes(b"source video data")
    calls = []
    def fake_run(command, **kwargs):
        calls.append(command)
        return SimpleNamespace(stdout=json.dumps({
            "streams": [
                {"codec_type": "video", "width": 720, "height": 1280},
                {"codec_type": "audio"},
            ],
            "format": {"duration": "30.17"},
        }))
    monkeypatch.setattr(studio_video_tools.subprocess, "run", fake_run)
    assert studio_video_tools.probe_owned_video(root=tmp_path, source=src) == {
        "duration_seconds": 30.17, "width": 720, "height": 1280,
        "audio_present": True, "size_bytes": len(b"source video data"),
        "source_verified_in_root": True,
    }
    assert calls[0][0] == "ffprobe"


def test_normalise_uses_bounded_argv_and_not_a_shell(monkeypatch, tmp_path):
    src = tmp_path / "source.mp4"
    src.write_bytes(b"source video data")
    output = tmp_path / "output"
    output.mkdir()
    probe_calls = []
    def fake_probe(*, root, source):
        probe_calls.append(source)
        return {"duration_seconds": 30.17 if source == src else 29.7}
    commands = []
    def fake_run(command, **kwargs):
        commands.append((command, kwargs))
        (output / "safe_clip.mp4").write_bytes(b"rendered")
    monkeypatch.setattr(studio_video_tools, "probe_owned_video", fake_probe)
    monkeypatch.setattr(studio_video_tools.subprocess, "run", fake_run)
    result = studio_video_tools.normalise_swap_source(
        owner_root=tmp_path, source=src, output_root=output,
        output_name="safe_clip",
    )
    cmd, opts = commands[0]
    assert cmd[0] == "ffmpeg"
    assert cmd[cmd.index("-t") + 1] == "29.700"
    assert "shell" not in opts
    assert result["is_character_swap"] is False
    assert result["publishing_granted"] is False
    assert len(probe_calls) == 2


@pytest.mark.parametrize("name", ["../escape", "foo.mp4", "", "a/b", "my clip"])
def test_normalise_rejects_unsafe_output_names(tmp_path, name):
    with pytest.raises(ValueError, match="output_name_invalid"):
        studio_video_tools.normalise_swap_source(
            owner_root=tmp_path, source=Path("/nonexistent"),
            output_root=tmp_path, output_name=name,
        )


def test_scene_21_rejects_wrong_clip_count(tmp_path):
    with pytest.raises(ValueError, match="requires_seven_clips"):
        studio_video_tools.assemble_scene_21(
            owner_root=tmp_path, sources=(), output_name="scene",
        )


def test_scene_21_rejects_duplicate_source(tmp_path):
    clip = tmp_path / "clip.mp4"
    clip.write_bytes(b"source")
    with pytest.raises(ValueError, match="distinct_clips"):
        studio_video_tools.assemble_scene_21(
            owner_root=tmp_path, sources=(clip,) * 7, output_name="scene",
        )


def test_scene_21_real_ffmpeg_picture_edit(tmp_path):
    import shutil
    import subprocess

    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        pytest.skip("local FFmpeg unavailable")
    sources = []
    for i, color in enumerate(("red", "green", "blue", "yellow", "white", "black", "purple")):
        path = tmp_path / f"shot{i}.mp4"
        subprocess.run(
            ["ffmpeg", "-v", "error", "-f", "lavfi", "-i",
             f"color=c={color}:s=160x90:r=24:d=4", "-c:v", "libx264",
             "-pix_fmt", "yuv420p", str(path)],
            check=True, capture_output=True, timeout=30,
        )
        sources.append(path)
    result = studio_video_tools.assemble_scene_21(
        owner_root=tmp_path, sources=tuple(sources), output_name="scene",
    )
    assert result["duration_seconds"] == 21
    assert result["frame_count"] == 504
    assert result["picture_edit_verified"] is True
    assert result["audio_mastered"] is False
    assert result["identity_verified"] is False
    assert result["published"] is False
    assert len(result["sha256"]) == 64
    assert (tmp_path / "scene.mp4").is_file()
    with pytest.raises(ValueError, match="output_exists"):
        studio_video_tools.assemble_scene_21(
            owner_root=tmp_path, sources=tuple(sources), output_name="scene",
        )
