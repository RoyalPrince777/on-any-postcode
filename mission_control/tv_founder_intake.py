"""Founder-only OAP TV film intake. Private storage; never publishes or streams."""
from __future__ import annotations

import hashlib
import os
import uuid
from pathlib import Path

MAX_VIDEO_BYTES = 25 * 1024 * 1024
ACCEPTED = {"video/mp4": b"ftyp", "video/webm": b"\x1aE\xdf\xa3"}


def intake(stream, *, content_type: str, title: str, owner_id: str, content_kind: str = "film") -> dict[str, object]:
    """Store a bounded, private first-party candidate, with no public access."""
    directory = os.environ.get("OAP_TV_PRIVATE_MEDIA_DIR", "").strip()
    root = Path(directory) if directory else None
    if root is None or not root.is_absolute() or not root.is_dir() or root.is_symlink():
        raise RuntimeError("tv_private_storage_not_configured")
    if not isinstance(title, str) or not 1 <= len(title.strip()) <= 180:
        raise ValueError("invalid_tv_title")
    if content_kind not in {"film", "clip", "trailer", "episode"}:
        raise ValueError("invalid_tv_content_kind")
    if content_type not in ACCEPTED:
        raise ValueError("unsupported_tv_media_type")
    try:
        owner = str(uuid.UUID(owner_id))
    except (ValueError, TypeError, AttributeError) as exc:
        raise ValueError("invalid_tv_owner") from exc
    data = stream.read(MAX_VIDEO_BYTES + 1)
    if not data or len(data) > MAX_VIDEO_BYTES:
        raise ValueError("invalid_tv_media_size")
    if content_type == "video/mp4" and not (len(data) >= 12 and data[4:8] == b"ftyp"):
        raise ValueError("tv_media_signature_mismatch")
    if content_type == "video/webm" and not data.startswith(ACCEPTED[content_type]):
        raise ValueError("tv_media_signature_mismatch")
    item_id = str(uuid.uuid4())
    suffix = ".mp4" if content_type == "video/mp4" else ".webm"
    # Create private from the first byte; never expose an intermediate
    # world-readable file or leave a partial candidate after a write failure.
    path = root / (item_id + suffix)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    fd = os.open(path, flags, 0o600)
    try:
        with os.fdopen(fd, "wb") as target:
            target.write(data)
            target.flush()
            os.fsync(target.fileno())
    except BaseException:
        path.unlink(missing_ok=True)
        raise
    return {
        "candidate_id": item_id,
        "title": title.strip(),
        "content_kind": content_kind,
        "owner_id": owner,
        "mime_type": content_type,
        "byte_size": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        "private_intake": True,
        "published": False,
        "playback_enabled": False,
        "rights_verified": False,
        "human_authority_final": True,
    }
