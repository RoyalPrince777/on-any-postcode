"""Bounded offline TripoSR checkpoint integrity check; never loads pickle or grants execution."""
from __future__ import annotations

import hashlib
import os
import stat
from pathlib import Path

CHECKPOINT_SIZE = 1677246742
CHECKPOINT_SHA256 = "429e2c6b22a0923967459de24d67f05962b235f79cde6b032aa7ed2ffcd970ee"


def _inspect_checkpoint(directory: Path, *, size: int, expected_sha256: str) -> dict:
    if not hasattr(os, "O_NOFOLLOW") or not hasattr(os, "O_DIRECTORY"):
        return {"status": "blocked", "reason": "safe_file_open_unavailable"}
    try:
        root = os.open(directory, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            fd = os.open("model.ckpt", os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                         dir_fd=root)
            with os.fdopen(fd, "rb") as stream:
                before = os.fstat(stream.fileno())
                if not stat.S_ISREG(before.st_mode) or before.st_size != size:
                    return {"status": "failed", "reason": "checkpoint_size_or_type_mismatch"}
                digest = hashlib.sha256()
                remaining = size
                while remaining:
                    chunk = stream.read(min(1024 * 1024, remaining))
                    if not chunk:
                        return {"status": "failed", "reason": "checkpoint_truncated"}
                    digest.update(chunk)
                    remaining -= len(chunk)
                after = os.fstat(stream.fileno())
                if (stream.read(1) or before.st_size != after.st_size
                        or before.st_mtime_ns != after.st_mtime_ns
                        or before.st_ctime_ns != after.st_ctime_ns):
                    return {"status": "failed", "reason": "checkpoint_changed"}
                if digest.hexdigest() != expected_sha256:
                    return {"status": "failed", "reason": "checkpoint_digest_mismatch"}
                return {"status": "matched", "sha256": expected_sha256, "size_bytes": size}
        finally:
            os.close(root)
    except OSError:
        return {"status": "blocked", "reason": "checkpoint_unavailable"}


def checkpoint_preflight() -> dict:
    """Inspect only the administrator-configured model directory, with no network."""
    base = {"checkpoint_integrity_matched": False, "runtime_verified": False,
            "execution_granted": False, "checkpoint_loaded": False,
            "founder_final_required": True,
            "remaining_gates": ["config_hash_review", "dino_config_pin",
                                "dependency_lock_and_audit", "isolated_worker",
                                "safe_weights_only_loading", "hardware_and_inference_proof"]}
    directory = os.environ.get("OAP_STUDIO_TRIPOSR_MODEL_DIR", "").strip()
    if not directory:
        return {**base, "status": "blocked", "reason": "model_directory_not_configured"}
    result = _inspect_checkpoint(Path(directory), size=CHECKPOINT_SIZE,
                                 expected_sha256=CHECKPOINT_SHA256)
    return {**base, "checkpoint": result, "status": "blocked",
            "checkpoint_integrity_matched": result["status"] == "matched"}
