"""Truth-gated offline/local routing package evidence for Map Intelligence.

This module does not download data, invent coverage, or claim that an offline
router is running. It only proves that an explicitly enabled local OSRM package
is physically present and non-empty in the current runtime.
"""
from __future__ import annotations

import hashlib
import os
import re
from pathlib import Path

REQUIRED_SUFFIXES = (
    ".osrm",
    ".osrm.nodes",
    ".osrm.edges",
    ".osrm.geometry",
    ".osrm.names",
    ".osrm.properties",
)
_OPTIONAL_SUFFIXES = (
    ".osrm.cells",
    ".osrm.datasource_names",
    ".osrm.mldgr",
    ".osrm.partition",
)
_PREFIX_RE = re.compile(r"^[A-Za-z0-9._-]{1,120}$")


def _enabled() -> bool:
    return os.environ.get("OAP_OFFLINE_ROUTING_ENABLED", "").strip().lower() == "true"


def _root() -> Path | None:
    raw = os.environ.get("OAP_OFFLINE_ROUTING_DATASET_ROOT", "").strip()
    if not raw:
        return None
    path = Path(raw).expanduser()
    return path if path.is_absolute() else None


def _prefix() -> str:
    value = os.environ.get("OAP_OFFLINE_ROUTING_PREFIX", "").strip()
    return value if _PREFIX_RE.fullmatch(value) else ""


def status() -> dict[str, object]:
    """Return bounded evidence for a local OSRM routing package."""
    root = _root()
    prefix = _prefix()
    enabled = _enabled()

    required_files: list[str] = []
    optional_files: list[str] = []
    missing_files: list[str] = []
    total_bytes = 0
    fingerprint_parts: list[str] = []

    if root is not None and prefix and root.is_dir():
        for suffix in REQUIRED_SUFFIXES:
            path = root / f"{prefix}{suffix}"
            if path.is_file() and path.stat().st_size > 0:
                size = path.stat().st_size
                required_files.append(path.name)
                total_bytes += size
                fingerprint_parts.append(f"{path.name}:{size}")
            else:
                missing_files.append(path.name)

        for suffix in _OPTIONAL_SUFFIXES:
            path = root / f"{prefix}{suffix}"
            if path.is_file() and path.stat().st_size > 0:
                size = path.stat().st_size
                optional_files.append(path.name)
                total_bytes += size
                fingerprint_parts.append(f"{path.name}:{size}")
    elif prefix:
        missing_files = [f"{prefix}{suffix}" for suffix in REQUIRED_SUFFIXES]

    package_present = bool(
        enabled
        and root is not None
        and root.is_dir()
        and prefix
        and not missing_files
        and len(required_files) == len(REQUIRED_SUFFIXES)
        and total_bytes > 0
    )
    fingerprint = (
        hashlib.sha256("|".join(sorted(fingerprint_parts)).encode("utf-8")).hexdigest()
        if package_present
        else None
    )
    return {
        "component": "OAP Offline Routing Package",
        "enabled": enabled,
        "dataset_root_configured": root is not None,
        "dataset_root_exists": bool(root and root.is_dir()),
        "package_prefix_configured": bool(prefix),
        "required_file_count": len(REQUIRED_SUFFIXES),
        "required_files_present": tuple(required_files),
        "optional_files_present": tuple(optional_files),
        "missing_required_files": tuple(missing_files),
        "package_bytes": total_bytes,
        "package_fingerprint_sha256": fingerprint,
        "package_present": package_present,
        "offline_local_routing_package_proven": package_present,
        "network_required_for_proof": False,
        "tracking_performed": False,
        "dispatch_performed": False,
        "payment_performed": False,
        "truth_rule": "Green only when the enabled runtime contains every required non-empty local routing package file.",
    }
