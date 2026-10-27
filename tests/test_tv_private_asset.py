"""Fail-closed local media integrity verification; no playback authority."""
import hashlib

import pytest

from mission_control.tv_private_asset import UntrustedMediaAsset, inspect_private_asset


def test_trusted_asset_requires_matching_bytes(tmp_path):
    media = b"approved private test asset"
    asset_id = "a" * 64
    digest = hashlib.sha256(media).hexdigest()
    (tmp_path / asset_id).write_bytes(media)
    proof = inspect_private_asset(tmp_path, asset_id, digest)
    assert proof["storage_integrity_proven"] is True
    assert proof["playback_enabled"] is False
    assert proof["size"] == len(media)


@pytest.mark.parametrize("asset_id", ["../outside", "", "A" * 64, "a" * 63, "a" * 65])
def test_reject_untrusted_asset_names(tmp_path, asset_id):
    with pytest.raises(UntrustedMediaAsset):
        inspect_private_asset(tmp_path, asset_id, "b" * 64)


def test_missing_and_tampered_assets_fail_closed(tmp_path):
    asset_id = "a" * 64
    with pytest.raises(UntrustedMediaAsset):
        inspect_private_asset(tmp_path, asset_id, "b" * 64)
    (tmp_path / asset_id).write_bytes(b"tampered")
    with pytest.raises(UntrustedMediaAsset):
        inspect_private_asset(tmp_path, asset_id, "b" * 64)


def test_symlink_cannot_escape_storage_root(tmp_path):
    root = tmp_path / "private"
    root.mkdir()
    external = tmp_path / "outside"
    external.write_bytes(b"external")
    asset_id = "a" * 64
    (root / asset_id).symlink_to(external)
    with pytest.raises(UntrustedMediaAsset):
        inspect_private_asset(root, asset_id, hashlib.sha256(b"external").hexdigest())


def test_empty_file_and_directory_are_not_media(tmp_path):
    asset_id = "a" * 64
    (tmp_path / asset_id).touch()
    with pytest.raises(UntrustedMediaAsset):
        inspect_private_asset(tmp_path, asset_id, hashlib.sha256(b"").hexdigest())
    (tmp_path / asset_id).unlink()
    (tmp_path / asset_id).mkdir()
    with pytest.raises(UntrustedMediaAsset):
        inspect_private_asset(tmp_path, asset_id, "b" * 64)


def test_oversized_sparse_file_fails_without_reading_contents(tmp_path):
    asset_id = "a" * 64
    with (tmp_path / asset_id).open("wb") as media:
        media.truncate(64 * 1024 * 1024 + 1)
    with pytest.raises(UntrustedMediaAsset, match="invalid_media_object"):
        inspect_private_asset(tmp_path, asset_id, "b" * 64)


def test_symlink_storage_root_fails_closed(tmp_path):
    genuine = tmp_path / "genuine"
    genuine.mkdir()
    alias = tmp_path / "alias"
    alias.symlink_to(genuine, target_is_directory=True)
    with pytest.raises(UntrustedMediaAsset, match="invalid_storage_root"):
        inspect_private_asset(alias, "a" * 64, "b" * 64)
