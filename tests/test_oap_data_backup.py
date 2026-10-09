"""Hathi backup verification stays read-only and does not claim restore proof."""
import hashlib

from mission_control.oap_data_backup import verify_backup_manifest


def test_backup_digest_check_never_claims_restore(tmp_path):
    path = tmp_path / "backup.bin"
    path.write_bytes(b"oap backup bytes")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    result = verify_backup_manifest(
        backup_path=str(path), expected_sha256=digest, allowed_root=str(tmp_path)
    )
    assert result["verified"] is True
    assert result["restore_test_passed"] is False
    assert result["destructive_actions_authorized"] is False


def test_mismatch_fails(tmp_path):
    path = tmp_path / "backup.bin"
    path.write_bytes(b"data")
    result = verify_backup_manifest(
        backup_path=str(path), expected_sha256="0" * 64, allowed_root=str(tmp_path)
    )
    assert result["verified"] is False


def test_outside_root_blocked(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    path = tmp_path / "outside"
    path.write_bytes(b"data")
    result = verify_backup_manifest(
        backup_path=str(path),
        expected_sha256=hashlib.sha256(b"data").hexdigest(),
        allowed_root=str(root),
    )
    assert result["reason"] == "outside_backup_root"
