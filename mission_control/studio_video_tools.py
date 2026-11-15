"""Bounded local video-probe and clip-normalisation helpers for private Studio jobs.

Use only after the owner's asset store has authorised the source. These helpers
do not perform an AI character swap, make remote provider requests or grant
credit spending. Rendering is performed on an authorised media worker.
"""
from __future__ import annotations

import json
import math
import subprocess
from pathlib import Path
from typing import Any

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
        raise ValueError("studio_video_metadata_invalid")
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
