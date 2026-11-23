"""OAP Studio: bounded first-party still-image + optional audio MP4 composition.

This is an optional local FFmpeg adapter, not AI generation, cloning, publishing,
or authority to operate on arbitrary files. Call only from an authenticated,
owner-scoped Studio worker with an already authorised asset directory.
No third-party source code is embedded.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import uuid
from pathlib import Path


class StudioRenderUnavailable(RuntimeError):
    """Fail closed when local rendering or output verification fails."""


_MAX_INPUT_BYTES = 100 * 1024 * 1024
_MAX_OUTPUT_BYTES = 200 * 1024 * 1024
_IMAGE_SUFFIXES = frozenset({".png", ".jpg", ".jpeg", ".webp"})
_AUDIO_SUFFIXES = frozenset({".wav", ".mp3", ".m4a", ".aac"})


def _owner_file(root: Path, name: str, suffixes: frozenset[str]) -> Path:
    if not isinstance(name, str) or not name or name != Path(name).name:
        raise ValueError("studio_asset_filename_invalid")
    path = root / name
    if path.is_symlink() or path.suffix.lower() not in suffixes or not path.is_file():
        raise ValueError("studio_asset_missing_or_unsupported")
    if not 0 < path.stat().st_size <= _MAX_INPUT_BYTES:
        raise ValueError("studio_asset_size_invalid")
    return path


def _verify_mp4(binary_path: Path, *, expected_seconds: int) -> None:
    """Require a decoder-readable video stream before declaring a render complete."""
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        raise StudioRenderUnavailable("studio_ffprobe_unavailable")
    try:
        result = subprocess.run(
            [
                ffprobe, "-v", "error", "-select_streams", "v:0",
                "-show_entries", "format=duration:stream=codec_type,width,height",
                "-of", "json", str(binary_path),
            ],
            stdin=subprocess.DEVNULL, capture_output=True, text=True,
            timeout=20, check=False,
        )
        if result.returncode:
            raise StudioRenderUnavailable("studio_mp4_probe_failed")
        metadata = json.loads(result.stdout)
        tracks = metadata.get("streams") or []
        duration = float((metadata.get("format") or {}).get("duration", 0))
        if not (
            tracks and tracks[0].get("codec_type") == "video"
            and int(tracks[0].get("width", 0)) > 0
            and int(tracks[0].get("height", 0)) > 0
            and 0 < duration <= expected_seconds + 0.2
        ):
            raise StudioRenderUnavailable("studio_mp4_probe_invalid")
    except (OSError, subprocess.TimeoutExpired, ValueError, TypeError, KeyError) as exc:
        raise StudioRenderUnavailable("studio_mp4_probe_failed") from exc


def render_still_video(
    *, owner_directory: str, image_name: str, output_name: str,
    seconds: int = 4, audio_name: str | None = None,
    ffmpeg_binary: str = "ffmpeg",
) -> dict[str, object]:
    """Render a 24fps MP4 from previously verified, owner-local assets.

    Deliberately exposes no URL, remote fetch, arbitrary filter graph or shell.
    Does not grant permission to copy/clone voices or publicly distribute media.
    """
    if type(seconds) is not int or not 1 <= seconds <= 30:
        raise ValueError("studio_render_duration_invalid")
    # A caller's directory is not itself evidence of ownership. The worker
    # must configure a private asset root and the target must be a direct
    # child directory under it; reject symlink traversal before resolving.
    private_root = os.environ.get("OAP_STUDIO_PRIVATE_ASSET_ROOT", "").strip()
    if not private_root:
        raise StudioRenderUnavailable("studio_private_asset_root_unconfigured")
    base = Path(private_root).absolute()
    candidate = Path(owner_directory).absolute()
    if (
        not base.is_dir() or base.is_symlink()
        or candidate.parent != base
        or candidate.is_symlink() or not candidate.is_dir()
        or candidate.resolve(strict=True).parent != base.resolve(strict=True)
    ):
        raise ValueError("studio_owner_directory_invalid")
    root = candidate
    source = _owner_file(root, image_name, _IMAGE_SUFFIXES)
    audio = _owner_file(root, audio_name, _AUDIO_SUFFIXES) if audio_name else None
    if not isinstance(output_name, str) or output_name != Path(output_name).name or not output_name.endswith(".mp4"):
        raise ValueError("studio_output_filename_invalid")
    target = root / output_name
    if target.exists() or target.is_symlink():
        raise ValueError("studio_output_already_exists")
    binary = shutil.which(ffmpeg_binary)
    if not binary:
        raise StudioRenderUnavailable("studio_ffmpeg_unavailable")
    temp = root / ("." + uuid.uuid4().hex + ".mp4")
    args = [binary, "-nostdin", "-hide_banner", "-loglevel", "error", "-n",
            "-loop", "1", "-framerate", "24", "-i", str(source)]
    if audio:
        args.extend(["-i", str(audio)])
    args.extend(["-t", str(seconds), "-c:v", "libx264", "-pix_fmt", "yuv420p"])
    if audio:
        args.extend(["-c:a", "aac", "-af", "apad"])
    else:
        args.append("-an")
    args.extend(["-movflags", "+faststart", str(temp)])
    try:
        result = subprocess.run(args, stdin=subprocess.DEVNULL, capture_output=True,
                                text=True, timeout=90, check=False)
        if result.returncode != 0 or not temp.is_file():
            raise StudioRenderUnavailable("studio_ffmpeg_render_failed")
        count = temp.stat().st_size
        if not 0 < count <= _MAX_OUTPUT_BYTES:
            raise StudioRenderUnavailable("studio_mp4_size_invalid")
        with temp.open("rb") as file:
            header = file.read(32)
        if b"ftyp" not in header[:16]:
            raise StudioRenderUnavailable("studio_mp4_header_invalid")
        _verify_mp4(temp, expected_seconds=seconds)
        # Avoid replacing any existing user asset.
        try:
            os.link(temp, target)
        except FileExistsError as exc:
            raise ValueError("studio_output_already_exists") from exc
        with target.open("rb") as file:
            digest = hashlib.file_digest(file, "sha256").hexdigest()
        return {"filename": output_name, "mime_type": "video/mp4",
                "size_bytes": count, "sha256": digest, "rendered": True,
                "published": False, "founder_final": True}
    except subprocess.TimeoutExpired as exc:
        raise StudioRenderUnavailable("studio_ffmpeg_timeout") from exc
    finally:
        temp.unlink(missing_ok=True)



def export_owned_gif_as_mp4(
    *, owner_directory: str, gif_name: str, output_name: str,
) -> dict[str, object]:
    """Export an existing owner-authorised GIF; NEVER claim AI generation.

    Requires the same configured private asset boundary as still-video
    rendering. No remote input, shell, publishing or external spending.
    """
    private_root = os.environ.get("OAP_STUDIO_PRIVATE_ASSET_ROOT", "").strip()
    if not private_root:
        raise StudioRenderUnavailable("studio_private_asset_root_unconfigured")
    base = Path(private_root).absolute()
    candidate = Path(owner_directory).absolute()
    if (
        not base.is_dir() or base.is_symlink()
        or candidate.parent != base or candidate.is_symlink()
        or not candidate.is_dir()
        or candidate.resolve(strict=True).parent != base.resolve(strict=True)
    ):
        raise ValueError("studio_owner_directory_invalid")
    source = _owner_file(candidate, gif_name, frozenset({".gif"}))
    if (
        not isinstance(output_name, str)
        or output_name != Path(output_name).name
        or not output_name.endswith(".mp4")
    ):
        raise ValueError("studio_output_filename_invalid")
    target = candidate / output_name
    if target.exists() or target.is_symlink():
        raise ValueError("studio_output_already_exists")
    ffmpeg = shutil.which("ffmpeg")
    ffprobe = shutil.which("ffprobe")
    if not ffmpeg or not ffprobe:
        raise StudioRenderUnavailable("studio_ffmpeg_unavailable")
    # Probe before rendering; bound duration and resolution to protect worker.
    try:
        check = subprocess.run(
            [ffprobe, "-v", "error", "-show_entries",
             "format=duration:stream=codec_type,width,height",
             "-of", "json", str(source)],
            stdin=subprocess.DEVNULL, capture_output=True, text=True,
            timeout=20, check=False,
        )
        if check.returncode:
            raise StudioRenderUnavailable("studio_gif_probe_failed")
        info = json.loads(check.stdout)
        streams = info.get("streams") or []
        video = next((s for s in streams if s.get("codec_type") == "video"), None)
        duration = float((info.get("format") or {}).get("duration") or 0)
        if (
            video is None or not 0 < duration <= 30
            or not 1 <= int(video.get("width", 0)) <= 1920
            or not 1 <= int(video.get("height", 0)) <= 1920
        ):
            raise StudioRenderUnavailable("studio_gif_probe_invalid")
    except (ValueError, TypeError, KeyError, OSError, subprocess.TimeoutExpired) as exc:
        raise StudioRenderUnavailable("studio_gif_probe_failed") from exc
    temp = candidate / ("." + uuid.uuid4().hex + ".mp4")
    try:
        result = subprocess.run(
            [ffmpeg, "-nostdin", "-hide_banner", "-loglevel", "error", "-n",
             "-stream_loop", "-1", "-i", str(source), "-t", f"{duration:.3f}",
             "-vf", "fps=25,format=yuv420p", "-c:v", "libx264",
             "-movflags", "+faststart", str(temp)],
            stdin=subprocess.DEVNULL, capture_output=True, timeout=90, check=False,
        )
        if result.returncode or not temp.is_file():
            raise StudioRenderUnavailable("studio_gif_export_failed")
        size = temp.stat().st_size
        if not 0 < size <= _MAX_OUTPUT_BYTES:
            raise StudioRenderUnavailable("studio_mp4_size_invalid")
        _verify_mp4(temp, expected_seconds=duration)
        try:
            os.link(temp, target)
        except FileExistsError as exc:
            raise ValueError("studio_output_already_exists") from exc
        with target.open("rb") as file:
            digest = hashlib.file_digest(file, "sha256").hexdigest()
        with source.open("rb") as file:
            source_digest = hashlib.file_digest(file, "sha256").hexdigest()
        return {
            "filename": output_name, "mime_type": "video/mp4",
            "sha256": digest, "source_sha256": source_digest,
            "size_bytes": size, "rendered": True, "ai_generated_in_smi": False,
            "kind": "existing_gif_export", "published": False,
            "payment_authorised": False, "founder_final": True,
        }
    except subprocess.TimeoutExpired as exc:
        raise StudioRenderUnavailable("studio_gif_export_timeout") from exc
    finally:
        temp.unlink(missing_ok=True)
