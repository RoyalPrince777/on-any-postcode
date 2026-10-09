"""OAP Drive private local storage adapter. Not a cloud provisioning claim."""
import hashlib
import os
from pathlib import Path
import tempfile
from .drive_manifest import verify_artifact_manifest

class DriveStorage:
    def __init__(self, root):
        self.root = Path(root).resolve()
        if not self.root.is_dir() or self.root.is_symlink():
            raise ValueError("Storage root must be a provisioned, real directory")

    def put(self, manifest, payload):
        if not verify_artifact_manifest(manifest, payload):
            raise ValueError("Invalid artifact integrity manifest")
        digest = manifest["sha256"]
        destination = self.root / digest
        if destination.is_symlink():
            raise ValueError("Symlink artifact rejected")
        if destination.exists():
            if destination.read_bytes() != payload:
                raise ValueError("Existing artifact mismatch")
            return digest
        fd, temp_name = tempfile.mkstemp(prefix=".oap-", dir=self.root)
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            os.chmod(temp_name, 0o600)
            if destination.exists() or destination.is_symlink():
                raise ValueError("Concurrent artifact conflict")
            os.replace(temp_name, destination)
        finally:
            if os.path.exists(temp_name):
                os.unlink(temp_name)
        return digest

    def get(self, manifest):
        digest = manifest.get("sha256", "") if isinstance(manifest, dict) else ""
        if not isinstance(digest, str) or len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
            raise ValueError("Invalid digest")
        path = self.root / digest
        if path.is_symlink() or not path.is_file():
            raise FileNotFoundError("Artifact unavailable")
        payload = path.read_bytes()
        if not verify_artifact_manifest(manifest, payload):
            raise ValueError("Stored artifact integrity failure")
        return payload
