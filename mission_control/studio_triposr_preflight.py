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


# Explicit administrator acquisition only; never invoked by a web request,
# health probe, scheduler or inference. No credentials or user asset uploads.
CHECKPOINT_URL = (
    "https://huggingface.co/stabilityai/TripoSR/resolve/"
    "c1cf7716aed5aa6c1c5e174657791ef0e1327bde/model.ckpt"
)


def acquire_checkpoint() -> dict:
    """Stage the public pinned artifact, verify, then publish locally without overwrite."""
    import shutil
    import subprocess
    import tempfile

    configured = os.environ.get("OAP_STUDIO_TRIPOSR_MODEL_DIR", "").strip()
    if not configured:
        return {"status": "blocked", "reason": "model_directory_not_configured"}
    root = Path(configured)
    if (not root.is_absolute() or not root.is_dir() or root.is_symlink()
            or root.resolve() != root
            or root.stat().st_mode & 0o077
            or not hasattr(os, "getuid") or root.stat().st_uid != os.getuid()):
        return {"status": "blocked", "reason": "private_model_directory_required"}
    existing = _inspect_checkpoint(root, size=CHECKPOINT_SIZE,
                                   expected_sha256=CHECKPOINT_SHA256)
    if existing["status"] == "matched":
        return {**existing, "downloaded": False, "execution_granted": False}
    if (root / "model.ckpt").exists() or (root / "model.ckpt").is_symlink():
        return {"status": "blocked", "reason": "existing_checkpoint_not_replaced"}
    if shutil.disk_usage(root).free < CHECKPOINT_SIZE + 64 * 1024 * 1024:
        return {"status": "blocked", "reason": "insufficient_disk"}
    curl = shutil.which("curl")
    if not curl:
        return {"status": "blocked", "reason": "curl_unavailable"}
    try:
        with tempfile.TemporaryDirectory(prefix=".triposr-", dir=root) as stage:
            target = Path(stage) / "model.ckpt"
            run = subprocess.run(
                [curl, "-q", "--fail", "--silent", "--show-error", "--location",
                 "--proto", "=https", "--proto-redir", "=https", "--max-redirs", "5",
                 "--connect-timeout", "15", "--max-time", "1800",
                 "--max-filesize", str(CHECKPOINT_SIZE),
                 "--output", str(target), CHECKPOINT_URL],
                stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL, timeout=1810, check=False,
            )
            if run.returncode:
                return {"status": "blocked", "reason": "checkpoint_download_failed"}
            verified = _inspect_checkpoint(Path(stage), size=CHECKPOINT_SIZE,
                                           expected_sha256=CHECKPOINT_SHA256)
            if verified["status"] != "matched":
                return verified
            target.chmod(0o600)
            os.link(target, root / "model.ckpt")
            return {**verified, "downloaded": True, "execution_granted": False,
                    "checkpoint_loaded": False, "runtime_verified": False}
    except (OSError, subprocess.TimeoutExpired):
        return {"status": "blocked", "reason": "checkpoint_acquisition_failed"}


if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--acquire", action="store_true",
                        help="Explicitly download the pinned public checkpoint; no inference")
    options = parser.parse_args()
    result = acquire_checkpoint() if options.acquire else checkpoint_preflight()
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result.get("status") == "matched" else 1)
