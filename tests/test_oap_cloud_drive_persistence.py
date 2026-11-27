"""Real filesystem persistence and failure tests for the isolated Drive adapter.

A temporary directory is NOT provisioned cloud storage. These tests prove only
local process-restart semantics and fail-closed integrity checks.
"""
import hashlib

import pytest

from oap_cloud.drive_storage import DriveStorage


def _manifest(payload):
    return {
        "kind": "build-log",
        "size_bytes": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
    }


def test_artifact_survives_new_storage_instance(tmp_path):
    root = tmp_path / "drive"
    root.mkdir()
    payload = b"persist-across-adapter-restart"
    manifest = _manifest(payload)

    first = DriveStorage(root)
    assert first.put(manifest, payload) == manifest["sha256"]
    del first

    # Recreate the adapter against the same real directory.
    reopened = DriveStorage(root)
    assert reopened.get(manifest) == payload
    assert reopened.put(manifest, payload) == manifest["sha256"]


def test_missing_storage_root_fails_closed(tmp_path):
    with pytest.raises(ValueError, match="real directory"):
        DriveStorage(tmp_path / "not-provisioned")


def test_existing_digest_collision_cannot_be_overwritten(tmp_path):
    payload = b"trusted-artifact"
    manifest = _manifest(payload)
    store = DriveStorage(tmp_path)
    digest_path = tmp_path / manifest["sha256"]
    digest_path.write_bytes(b"tampered-artifact")

    with pytest.raises(ValueError, match="Existing artifact mismatch"):
        store.put(manifest, payload)
    assert digest_path.read_bytes() == b"tampered-artifact"


def test_reopened_adapter_detects_disk_tampering(tmp_path):
    payload = b"original-artifact"
    manifest = _manifest(payload)
    DriveStorage(tmp_path).put(manifest, payload)
    (tmp_path / manifest["sha256"]).write_bytes(b"changed-artifact!!")

    with pytest.raises(ValueError, match="integrity"):
        DriveStorage(tmp_path).get(manifest)
