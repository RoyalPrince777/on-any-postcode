"""Founder-only TDA staging. No publication authority or public writes."""
from __future__ import annotations

import base64
import hashlib
import json
import os
import stat
from pathlib import Path

FILES = {"index.html": 128 * 1024, "game.js": 1024 * 1024,
         "babylon.js": 16 * 1024 * 1024}
LOADER = "s.src=url;"
PUBLIC_ROUTE = "/arena/tda-london/"


def _read(root: int, name: str, limit: int) -> bytes:
    fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=root)
    with os.fdopen(fd, "rb") as stream:
        info = os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode) or not 0 < info.st_size <= limit:
            raise ValueError("invalid_candidate_file")
        data = stream.read(limit + 1)
        if len(data) != info.st_size or len(data) > limit:
            raise ValueError("candidate_file_changed")
        return data


def candidate(instance: str) -> tuple[str, dict[str, bytes]]:
    """Read a bounded, private, locally staged snapshot and verify its manifest."""
    path = Path(instance) / "tda-preview"
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        info = os.fstat(fd)
        if info.st_mode & 0o077 or info.st_uid != os.getuid():
            raise ValueError("private_candidate_directory_required")
        manifest = json.loads(_read(fd, "manifest.json", 4096))
        if not isinstance(manifest, dict) or set(manifest) != set(FILES):
            raise ValueError("candidate_manifest_invalid")
        data = {name: _read(fd, name, limit) for name, limit in FILES.items()}
        hashes = {name: hashlib.sha256(value).hexdigest() for name, value in data.items()}
        if hashes != manifest:
            raise ValueError("candidate_hash_mismatch")
        version = hashlib.sha256(json.dumps(hashes, sort_keys=True).encode()).hexdigest()
        return version, data
    finally:
        os.close(fd)


def document(data: dict[str, bytes]) -> str:
    """Reuse the original loader with in-memory scripts and an opaque sandbox."""
    html = data["index.html"].decode("utf-8")
    if html.count(LOADER) != 1 or html.count("<script>") != 1:
        raise ValueError("candidate_loader_unrecognized")
    assets = {
        "game.js": base64.b64encode(data["game.js"]).decode("ascii"),
        "vendor/babylon.js": base64.b64encode(data["babylon.js"]).decode("ascii"),
    }
    bootstrap = "<script>const TDA_ASSETS=" + json.dumps(assets) + ";</script>"
    loader = (
        "s.src=URL.createObjectURL(new Blob([Uint8Array.from(atob(TDA_ASSETS[url]),"
        "c=>c.charCodeAt(0))],{type:'text/javascript'}));"
    )
    return html.replace("<script>", bootstrap + "<script>", 1).replace(LOADER, loader, 1)


def publication_preflight(instance: str, expected: str) -> dict:
    """Check the exact staged version; refuse until canonical promotion is wired."""
    version, data = candidate(instance)
    document(data)
    if expected != version:
        raise ValueError("candidate_version_changed")
    return {
        "status": "blocked",
        "version": version,
        "public_route": PUBLIC_ROUTE,
        "published": False,
        "execution_granted": False,
        "blockers": ["independent_device_runtime_proof_required",
                     "canonical_guardian_hrm_green_gate_publisher_not_connected",
                     "founder_final_for_exact_version_required"],
    }
