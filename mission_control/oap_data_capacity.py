"""Read-only, first-party filesystem capacity measurement for OAP Data.

Only measure an explicitly configured existing storage root. This does not
provision storage, mount remote volumes, or promise atomic reservations.
"""
from __future__ import annotations

import os
import shutil
from pathlib import Path

from mission_control.oap_data_storage import StorageCapacity, admission


def measure_storage_root(root: str | None) -> StorageCapacity | None:
    if not root or not isinstance(root, str):
        return None
    path = Path(root)
    if not path.is_absolute() or not path.is_dir() or path.is_symlink():
        return None
    try:
        usage = shutil.disk_usage(path)
    except OSError:
        return None
    return StorageCapacity(
        total_bytes=usage.total,
        used_bytes=usage.used,
        measured=True,
    )


def configured_storage_capacity() -> StorageCapacity | None:
    return measure_storage_root(os.environ.get("OAP_DATA_STORAGE_ROOT"))


def preflight_import(*, requested_bytes: int, system: str = "music") -> dict[str, object]:
    """Return a non-binding storage gate; recheck at the actual write boundary."""
    return admission(
        system=system,
        requested_bytes=requested_bytes,
        capacity=configured_storage_capacity(),
    )
