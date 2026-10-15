"""First-party OAP Cloud private object core: no public routes or external storage.

Local filesystem candidate only. Not suitable for production without durable storage,
malware scanning, audited access controls and independently verified backups.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
from uuid import uuid4

MAX_BYTES = 5 * 1024 * 1024


class CloudAccessError(PermissionError):
    pass


def _owner(owner_id: str) -> str:
    if not isinstance(owner_id, str) or not owner_id.strip() or len(owner_id) > 128:
        raise ValueError("valid owner required")
    return hashlib.sha256(owner_id.encode("utf-8")).hexdigest()


def _object_id(object_id: str) -> str:
    if not isinstance(object_id, str) or len(object_id) != 32:
        raise ValueError("invalid object id")
    try:
        int(object_id, 16)
    except ValueError as exc:
        raise ValueError("invalid object id") from exc
    return object_id.lower()


class PrivateObjectStore:
    """Private-only object storage. Caller identity must be server-authenticated."""

    def __init__(self, root: Path):
        self.root = Path(root)
        if self.root.is_symlink():
            raise CloudAccessError('storage root cannot be a symlink')

    def put(self, *, owner_id: str, authenticated_owner_id: str, data: bytes) -> str:
        if not owner_id or owner_id != authenticated_owner_id:
            raise CloudAccessError("owner mismatch")
        owner_key = _owner(owner_id)
        if not isinstance(data, bytes) or len(data) > MAX_BYTES:
            raise ValueError("invalid object bytes or size")
        directory = self.root / "personal" / owner_key
        directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        if directory.is_symlink() or (self.root / 'personal').is_symlink():
            raise CloudAccessError('storage directory cannot be a symlink')
        object_id = uuid4().hex
        path = directory / object_id
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        fd = os.open(path, flags, 0o600)
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
        return object_id

    def get(self, *, owner_id: str, authenticated_owner_id: str, object_id: str) -> bytes:
        if not owner_id or owner_id != authenticated_owner_id:
            raise CloudAccessError("owner mismatch")
        owner_key = _owner(owner_id)
        path = self.root / "personal" / owner_key / _object_id(object_id)
        if (self.root / 'personal').is_symlink() or path.parent.is_symlink():
            raise CloudAccessError('storage directory cannot be a symlink')
        # No-follow open closes the symlink replacement race at the final component.
        flags = os.O_RDONLY
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        if path.is_symlink():
            raise CloudAccessError("symlink forbidden")
        try:
            fd = os.open(path, flags)
        except OSError as exc:
            raise CloudAccessError("object unavailable or unsafe") from exc
        with os.fdopen(fd, "rb") as stream:
            data = stream.read(MAX_BYTES + 1)
        if len(data) > MAX_BYTES:
            raise CloudAccessError("object exceeds limit")
        return data
