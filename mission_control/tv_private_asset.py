"""Trusted, read-only local OAP TV asset inspection for future private playback.

This is NOT an upload, playback, or public endpoint. Asset identifiers come from
trusted server-side records; this helper never accepts a client-chosen path.
"""
from __future__ import annotations

import hashlib
import os
import re
import stat
from pathlib import Path

_ASSET_ID = re.compile(r"[a-f0-9]{64}", re.ASCII)
_MAX_ASSET_BYTES = 64 * 1024 * 1024


class UntrustedMediaAsset(ValueError):
    """Media object lacks bounded trusted-local-storage proof."""


def inspect_private_asset(root: Path, asset_id: str, expected_sha256: str) -> dict[str, object]:
    """Inspect a stored asset without granting rights or returning media bytes.

    The caller must provide a server-owned root, asset ID and recorded digest.
    Files are regular, non-symlink objects under root, size-bounded, and hashed.
    """
    if not isinstance(asset_id, str) or _ASSET_ID.fullmatch(asset_id) is None:
        raise UntrustedMediaAsset("invalid_asset_id")
    if not isinstance(expected_sha256, str) or _ASSET_ID.fullmatch(expected_sha256) is None:
        raise UntrustedMediaAsset("invalid_expected_digest")
    if not isinstance(root, Path) or not root.is_dir() or root.is_symlink():
        raise UntrustedMediaAsset("invalid_storage_root")
    descriptor = None
    try:
        descriptor = os.open(root / asset_id, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode) or not (0 < metadata.st_size <= _MAX_ASSET_BYTES):
            raise UntrustedMediaAsset("invalid_media_object")
        digest = hashlib.sha256()
        size = 0
        while True:
            block = os.read(descriptor, 1024 * 1024)
            if not block:
                break
            size += len(block)
            if size > _MAX_ASSET_BYTES:
                raise UntrustedMediaAsset("media_size_exceeded")
            digest.update(block)
        if size != metadata.st_size or digest.hexdigest() != expected_sha256:
            raise UntrustedMediaAsset("media_integrity_mismatch")
        return {"asset_id": asset_id, "sha256": expected_sha256, "size": size,
                "storage_integrity_proven": True, "playback_enabled": False}
    except OSError as exc:
        raise UntrustedMediaAsset("media_unavailable") from exc
    finally:
        if descriptor is not None:
            os.close(descriptor)
