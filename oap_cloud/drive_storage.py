"""OAP Drive private local storage adapter. Not a cloud provisioning claim."""
import os
from pathlib import Path
import tempfile
from .drive_manifest import verify_artifact_manifest

MAX_ARTIFACT_BYTES = 15_000_000


class DriveStorage:
    def __init__(self, root):
        original = Path(root)
        if original.is_symlink():
            raise ValueError("Symlink storage root rejected")
        self.root = original.resolve()
        if not self.root.is_dir() or self.root.is_symlink():
            raise ValueError("Storage root must be a provisioned, real directory")

    def put(self, manifest, payload):
        if len(payload) > MAX_ARTIFACT_BYTES or not verify_artifact_manifest(manifest, payload):
            raise ValueError("Invalid artifact integrity manifest")
        digest = manifest["sha256"]
        destination = self.root / digest
        if destination.is_symlink():
            raise ValueError("Symlink artifact rejected")
        if destination.exists():
            if not destination.is_file() or destination.read_bytes() != payload:
                raise ValueError("Existing artifact mismatch")
            return digest
        fd, temp_name = tempfile.mkstemp(prefix=".oap-", dir=self.root)
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            os.chmod(temp_name, 0o600)
            # Hard-link creation is atomic and fails if another writer won.
            # os.replace would overwrite an artifact after a TOCTOU race.
            try:
                os.link(temp_name, destination, follow_symlinks=False)
            except FileExistsError:
                if destination.is_symlink() or not destination.is_file() or destination.read_bytes() != payload:
                    raise ValueError("Concurrent artifact conflict")
        finally:
            if os.path.exists(temp_name):
                os.unlink(temp_name)
        return digest

    def get(self, manifest):
        digest = manifest.get("sha256", "") if isinstance(manifest, dict) else ""
        if not isinstance(digest, str) or len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
            raise ValueError("Invalid digest")
        expected_size = manifest.get("size_bytes")
        if type(expected_size) is not int or not 0 <= expected_size <= MAX_ARTIFACT_BYTES:
            raise ValueError("Artifact size outside storage bounds")
        path = self.root / digest
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
        try:
            fd = os.open(path, flags)
        except OSError as exc:
            raise FileNotFoundError("Artifact unavailable") from exc
        try:
            import stat

            details = os.fstat(fd)
            if not stat.S_ISREG(details.st_mode) or details.st_size != expected_size:
                raise ValueError("Stored artifact size or type mismatch")
            with os.fdopen(fd, "rb", closefd=False) as handle:
                payload = handle.read(MAX_ARTIFACT_BYTES + 1)
        finally:
            os.close(fd)
        if not verify_artifact_manifest(manifest, payload):
            raise ValueError("Stored artifact integrity failure")
        return payload
