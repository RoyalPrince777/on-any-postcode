"""Bounded local video-probe and clip-normalisation helpers for private Studio jobs.

Use only after the owner's asset store has authorised the source. These helpers
do not perform an AI character swap, make remote provider requests or grant
credit spending. Rendering is performed on an authorised media worker.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import subprocess
from pathlib import Path
from typing import Any
from uuid import uuid4

MAX_SOURCE_BYTES = 100 * 1024 * 1024
MAX_INPUT_SECONDS = 600
MAX_OUTPUT_SECONDS = 30.0


def _owned_path(root: Path, source: Path) -> Path:
    trusted_root = root.resolve(strict=True)
    path = source.resolve(strict=True)
    if trusted_root not in path.parents or not path.is_file():
        raise ValueError("studio_video_unowned_path")
    if path.stat().st_size < 1 or path.stat().st_size > MAX_SOURCE_BYTES:
        raise ValueError("studio_video_size_invalid")
    if path.suffix.lower() not in {".mp4", ".mov", ".webm"}:
        raise ValueError("studio_video_extension_unsupported")
    return path


def probe_owned_video(*, root: Path, source: Path) -> dict[str, Any]:
    """Probe only a trusted, owner-verified local file within a private root."""
    path = _owned_path(root, source)
    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "error", "-show_entries",
                "format=duration:stream=index,codec_type,width,height,r_frame_rate",
                "-of", "json", str(path),
            ],
            check=True, capture_output=True, text=True, timeout=20,
        )
        payload = json.loads(result.stdout)
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired, ValueError) as exc:
        raise RuntimeError("studio_ffprobe_failed") from exc
    if not isinstance(payload, dict):
        raise TypeError("studio_video_metadata_invalid")
    streams = payload.get("streams") or []
    video = next((item for item in streams if item.get("codec_type") == "video"), None)
    if not video:
        raise ValueError("studio_video_stream_missing")
    try:
        duration = float((payload.get("format") or {}).get("duration", 0))
        width, height = int(video["width"]), int(video["height"])
    except (TypeError, KeyError, ValueError) as exc:
        raise ValueError("studio_video_metadata_invalid") from exc
    if not math.isfinite(duration) or duration <= 0 or duration > MAX_INPUT_SECONDS:
        raise ValueError("studio_video_duration_invalid")
    if not (1 <= width <= 4096 and 1 <= height <= 4096):
        raise ValueError("studio_video_dimensions_invalid")
    return {
        "duration_seconds": duration,
        "width": width,
        "height": height,
        "audio_present": any(item.get("codec_type") == "audio" for item in streams),
        "size_bytes": path.stat().st_size,
        "source_verified_in_root": True,
    }


def normalise_swap_source(
    *, owner_root: Path, source: Path, output_root: Path,
    output_name: str, max_seconds: float = 29.7,
) -> dict[str, Any]:
    """Bounded, no-shell conversion to MP4; output remains private/unpublished.

    Caller supplies a UUID-derived output_name (ASCII alphanumeric, underscore,
    hyphen only); worker must ensure output root is private and owner-scoped.
    """
    if not output_name or not all(char.isascii() and (char.isalnum() or char in "_-") for char in output_name):
        raise ValueError("studio_video_output_name_invalid")
    if not (4 <= max_seconds <= MAX_OUTPUT_SECONDS) or not math.isfinite(max_seconds):
        raise ValueError("studio_video_output_duration_invalid")
    path = _owned_path(owner_root, source)
    metadata = probe_owned_video(root=owner_root, source=path)
    if metadata["duration_seconds"] < 4:
        raise ValueError("studio_video_source_too_short")
    duration = min(float(max_seconds), metadata["duration_seconds"])
    trusted_output = output_root.resolve(strict=True)
    if not trusted_output.is_dir() or trusted_output.is_symlink():
        raise ValueError("studio_video_output_root_invalid")
    destination = trusted_output / f"{output_name}.mp4"
    if destination.exists() or destination.is_symlink():
        raise ValueError("studio_video_output_exists")
    command = [
        "ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error",
        "-i", str(path), "-t", f"{duration:.3f}",
        "-map", "0:v:0", "-map", "0:a?",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
        "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k",
        "-movflags", "+faststart", str(destination),
    ]
    try:
        subprocess.run(command, check=True, capture_output=True, timeout=180)
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        destination.unlink(missing_ok=True)
        raise RuntimeError("studio_ffmpeg_normalise_failed") from exc
    try:
        output = probe_owned_video(root=trusted_output, source=destination)
        if output["duration_seconds"] > 30.0 or output["duration_seconds"] < 4:
            raise ValueError("studio_video_output_duration_invalid")
    except (ValueError, RuntimeError):
        destination.unlink(missing_ok=True)
        raise
    return {
        "path": str(destination),
        "metadata": output,
        "kind": "local_clip",
        "is_character_swap": False,
        "render_submitted": False,
        "publishing_granted": False,
        "founder_review_required": True,
    }


def assemble_scene_21(
    *, owner_root: Path, sources: tuple[Path, ...], output_name: str,
    profile: str = "standard",
) -> dict[str, Any]:
    """Assemble seven authorised local clips; caller must verify owner and rights.

    Allowlisted 720p or 1080p/24fps silent picture edit. No provider calls, audio mastering,
    publishing, character-identity approval or new execution authority.
    """
    profiles = {"standard": (1280, 720), "cinema": (1920, 1080), "cinema_vertical": (1080, 1920)}
    if profile not in profiles:
        raise ValueError("studio_scene_profile_unsupported")
    width, height = profiles[profile]
    if len(sources) != 7:
        raise ValueError("studio_scene_requires_seven_clips")
    if not output_name or not all(
        char.isascii() and (char.isalnum() or char in "_-") for char in output_name
    ):
        raise ValueError("studio_video_output_name_invalid")
    root = owner_root.resolve(strict=True)
    paths = tuple(_owned_path(root, source) for source in sources)
    if len(set(paths)) != 7:
        raise ValueError("studio_scene_requires_distinct_clips")
    for path in paths:
        if probe_owned_video(root=root, source=path)["duration_seconds"] < 3:
            raise ValueError("studio_scene_clip_too_short")
    target = root / f"{output_name}.mp4"
    if target.exists() or target.is_symlink():
        raise ValueError("studio_video_output_exists")
    temp = root / f".{uuid4().hex}.mp4"
    command = ["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-n"]
    for path in paths:
        command.extend(["-protocol_whitelist", "file", "-i", str(path)])
    filters = [
        f"[{i}:v:0]setpts=PTS-STARTPTS,fps=24,trim=end_frame=72,"
        f"scale={width}:{height}:force_original_aspect_ratio=decrease:force_divisible_by=2,"
        f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,setsar=1,format=yuv420p,"
        f"setpts=PTS-STARTPTS[v{i}]"
        for i in range(7)
    ]
    filters.append("".join(f"[v{i}]" for i in range(7)) + "concat=n=7:v=1:a=0[out]")
    command.extend([
        "-filter_complex_threads", "1", "-filter_complex", ";".join(filters),
        "-map", "[out]", "-an", "-c:v", "libx264", "-preset", "veryfast",
        "-movflags", "+faststart", str(temp),
    ])
    try:
        subprocess.run(command, check=True, capture_output=True, timeout=180)
        metadata = probe_owned_video(root=root, source=temp)
        if (
            abs(metadata["duration_seconds"] - 21) > 0.01
            or metadata["width"] != width or metadata["height"] != height
            or metadata["audio_present"]
        ):
            raise ValueError("studio_scene_output_not_21_seconds")
        # Count decoded frames, not merely container metadata.
        frames = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0", "-count_frames",
             "-show_entries", "stream=nb_read_frames", "-of",
             "default=noprint_wrappers=1:nokey=1", str(temp)],
            check=True, capture_output=True, text=True, timeout=60,
        )
        if frames.stdout.strip() != "504":
            raise ValueError("studio_scene_frame_count_invalid")
        with temp.open("rb") as handle:
            digest = hashlib.file_digest(handle, "sha256").hexdigest()
        os.link(temp, target)
        return {
            "filename": target.name,
            "sha256": digest,
            "duration_seconds": metadata["duration_seconds"],
            "frame_count": 504,
            "profile": profile,
            "width": width,
            "height": height,
            "native_source_resolution_verified": False,
            "cinematic_quality_verified": False,
            "picture_edit_verified": True,
            "audio_mastered": False,
            "identity_verified": False,
            "published": False,
            "founder_review_required": True,
        }
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        raise RuntimeError("studio_scene_assembly_failed") from exc
    finally:
        temp.unlink(missing_ok=True)
