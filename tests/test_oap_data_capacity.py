"""OAP Data measured filesystem storage preflight."""
from mission_control.oap_data_capacity import (
    configured_storage_capacity,
    measure_storage_root,
    preflight_import,
)


def test_missing_root_fails_closed(monkeypatch):
    monkeypatch.delenv("OAP_DATA_STORAGE_ROOT", raising=False)
    assert configured_storage_capacity() is None
    assert preflight_import(requested_bytes=1)["reason"] == "capacity_unverified"


def test_real_existing_root_is_measured(tmp_path):
    cap = measure_storage_root(str(tmp_path))
    assert cap is not None
    assert cap.measured is True
    assert cap.total_bytes >= cap.used_bytes >= 0


def test_relative_and_missing_roots_not_measured(tmp_path):
    assert measure_storage_root("relative/path") is None
    assert measure_storage_root(str(tmp_path / "missing")) is None


def test_symlink_root_rejected(tmp_path):
    target = tmp_path / "target"
    target.mkdir()
    link = tmp_path / "link"
    link.symlink_to(target, target_is_directory=True)
    assert measure_storage_root(str(link)) is None
