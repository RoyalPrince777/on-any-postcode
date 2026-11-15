"""OAP Studio: bounded first-party still-image + optional audio MP4 composition.

This is an optional local FFmpeg adapter, not AI generation, cloning, publishing,
or authority to operate on arbitrary files. Call only from an authenticated,
owner-scoped Studio worker with an already authorised asset directory.
No third-party source code is embedded.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import uuid


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
    root = Path(owner_directory).resolve(strict=True)
    if not root.is_dir() or root.is_symlink():
        raise ValueError("studio_owner_directory_invalid")
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
