"""Private OAP Drive artifact manifest validation (no storage backend provisioned)."""
import hashlib
import re

SHA256 = re.compile(r"^[0-9a-f]{64}$")
ALLOWED = {"founder-debug-apk", "android-debug-apk", "os-emulator-image", "build-log"}

def verify_artifact_manifest(manifest: dict, payload: bytes) -> bool:
    """Verify a release artifact's declared type, byte count and SHA-256 digest."""
    if not isinstance(manifest, dict) or not isinstance(payload, bytes):
        return False
    if manifest.get("kind") not in ALLOWED:
        return False
    digest = manifest.get("sha256")
    if not isinstance(digest, str) or not SHA256.fullmatch(digest):
        return False
    size = manifest.get("size_bytes")
    if type(size) is not int or size < 0 or size != len(payload):
        return False
    return hashlib.sha256(payload).hexdigest() == digest
