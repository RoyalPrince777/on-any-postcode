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


def test_reject_symlink_storage_root(tmp_path):
    real_root = tmp_path / "real"
    real_root.mkdir()
    link_root = tmp_path / "linked"
    link_root.symlink_to(real_root, target_is_directory=True)
    with pytest.raises(ValueError, match="Symlink storage root"):
        DriveStorage(link_root)


def test_reject_directory_at_digest_path(tmp_path):
    store = DriveStorage(tmp_path)
    data = b"directory-collision"
    manifest = {"kind": "build-log", "size_bytes": len(data),
                "sha256": hashlib.sha256(data).hexdigest()}
    (tmp_path / manifest["sha256"]).mkdir()
    with pytest.raises(ValueError, match="Existing artifact mismatch"):
        store.put(manifest, data)


def test_reject_oversized_retrieval_manifest(tmp_path):
    from oap_cloud.drive_storage import MAX_ARTIFACT_BYTES

    store = DriveStorage(tmp_path)
    manifest = {"kind": "build-log", "size_bytes": MAX_ARTIFACT_BYTES + 1,
                "sha256": "a" * 64}
    with pytest.raises(ValueError, match="outside storage bounds"):
        store.get(manifest)


def test_reject_directory_on_retrieval(tmp_path):
    store = DriveStorage(tmp_path)
    manifest = {"kind": "build-log", "size_bytes": 0, "sha256": "b" * 64}
    (tmp_path / manifest["sha256"]).mkdir()
    with pytest.raises(ValueError, match="integrity"):
        store.get(manifest)
