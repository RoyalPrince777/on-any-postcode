import hashlib

import pytest

from oap_cloud.drive_storage import DriveStorage


def test_store_and_retrieve_verified_artifact(tmp_path):
    store = DriveStorage(tmp_path)
    data = b"oap-debug-apk"
    manifest = {"kind": "founder-debug-apk", "size_bytes": len(data),
                "sha256": hashlib.sha256(data).hexdigest()}
    assert store.put(manifest, data) == manifest["sha256"]
    assert store.get(manifest) == data
    (tmp_path / manifest["sha256"]).write_bytes(b"corrupt")
    with pytest.raises(ValueError, match="integrity"):
        store.get(manifest)

def test_reject_symlink_artifact(tmp_path):
    store = DriveStorage(tmp_path)
    data = b"data"
    manifest = {"kind": "build-log", "size_bytes": len(data),
                "sha256": hashlib.sha256(data).hexdigest()}
    target = tmp_path / "target"
    target.write_bytes(data)
    (tmp_path / manifest["sha256"]).symlink_to(target)
    with pytest.raises(ValueError, match="Symlink"):
        store.put(manifest, data)
    with pytest.raises(FileNotFoundError):
        store.get(manifest)
