"""First-party OAP Cloud private object core: no public routes or external storage.

Local filesystem candidate only. Not suitable for production without durable storage,
malware scanning, audited access controls and independently verified backups.
"""
from __future__ import annotations

import hashlib
import os
import stat
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
    """Local private storage candidate; caller identity must be server-authenticated.

    All filesystem traversal after root uses directory descriptors with O_NOFOLLOW.
    POSIX-only: refuses operation on platforms without descriptor-relative opens.
    """

    def __init__(self, root: Path):
        self.root = Path(root)
        if not hasattr(os, "O_NOFOLLOW") or not hasattr(os, "O_DIRECTORY"):
            raise CloudAccessError("secure directory operations unavailable")

    def _owner_directory(self, owner_id: str, *, create: bool):
        from contextlib import ExitStack

        stack = ExitStack()
        try:
            root_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
            current = os.open(self.root, root_flags)
            stack.callback(os.close, current)
            for name in ("personal", _owner(owner_id)):
                if create:
                    try:
                        os.mkdir(name, mode=0o700, dir_fd=current)
                    except FileExistsError:
                        pass
                child = os.open(name, root_flags, dir_fd=current)
                info = os.fstat(child)
                if info.st_mode & 0o077:
                    os.close(child)
                    raise CloudAccessError("storage directory permissions too broad")
                stack.callback(os.close, child)
                current = child
            return stack, current
        except BaseException:
            stack.close()
            raise

    def put(self, *, owner_id: str, authenticated_owner_id: str, data: bytes) -> str:
        if not owner_id or owner_id != authenticated_owner_id:
            raise CloudAccessError("owner mismatch")
        if not isinstance(data, bytes) or len(data) > MAX_BYTES:
            raise ValueError("invalid object bytes or size")
        stack, directory_fd = self._owner_directory(owner_id, create=True)
        with stack:
            object_id = uuid4().hex
            flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW
            fd = os.open(object_id, flags, 0o600, dir_fd=directory_fd)
            try:
                with os.fdopen(fd, "wb") as stream:
                    stream.write(data)
            except BaseException:
                os.unlink(object_id, dir_fd=directory_fd)
                raise
            return object_id

    def get(self, *, owner_id: str, authenticated_owner_id: str, object_id: str) -> bytes:
        if not owner_id or owner_id != authenticated_owner_id:
            raise CloudAccessError("owner mismatch")
        object_id = _object_id(object_id)
        try:
            stack, directory_fd = self._owner_directory(owner_id, create=False)
            with stack:
                fd = os.open(object_id, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory_fd)
                with os.fdopen(fd, "rb") as stream:
                    if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                        raise CloudAccessError("not a regular object")
                    data = stream.read(MAX_BYTES + 1)
                if len(data) > MAX_BYTES:
                    raise CloudAccessError("object exceeds limit")
                return data
        except OSError as exc:
            raise CloudAccessError("object unavailable or unsafe") from exc
