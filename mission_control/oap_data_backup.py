"""Colonel Hathi: inspect a backup manifest without modifying stored data.

This validates manifest shape and a supplied digest; it does not prove the
backup is recoverable. Restore proof requires an independent actual restore.
"""
from __future__ import annotations

import hashlib
from pathlib import Path


def verify_backup_manifest(
    *, backup_path: str, expected_sha256: str, allowed_root: str
) -> dict[str, object]:
    """Read-only SHA-256 validation inside a configured backup directory."""
    root = Path(allowed_root).resolve(strict=True)
    target = Path(backup_path)
    if not target.is_absolute() or not target.is_file() or target.is_symlink():
        return {"verified": False, "reason": "invalid_backup_path"}
    resolved = target.resolve(strict=True)
    if not resolved.is_relative_to(root) or not root.is_dir():
        return {"verified": False, "reason": "outside_backup_root"}
    if len(expected_sha256) != 64 or any(c not in "0123456789abcdef" for c in expected_sha256):
        return {"verified": False, "reason": "invalid_digest"}
    digest = hashlib.sha256()
    with resolved.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    match = digest.hexdigest() == expected_sha256
    return {
        "verified": match,
        "reason": "digest_match" if match else "digest_mismatch",
        "restore_test_passed": False,
        "destructive_actions_authorized": False,
    }
