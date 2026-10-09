"""Founder storage report truth-mode tests."""
from mission_control.oap_data_founder_report import founder_storage_report


def test_no_config_does_not_claim_storage_or_recovery(monkeypatch):
    monkeypatch.delenv("OAP_DATA_STORAGE_ROOT", raising=False)
    report = founder_storage_report()
    assert report["storage"]["measured"] is False
    assert report["storage"]["total_bytes"] is None
    assert report["hathi"]["ready"] is False
    assert report["production_ready"] is False


def test_real_storage_measurement_does_not_imply_recovery(monkeypatch, tmp_path):
    monkeypatch.setenv("OAP_DATA_STORAGE_ROOT", str(tmp_path))
    report = founder_storage_report()
    assert report["storage"]["measured"] is True
    assert report["hathi"]["ready"] is False
    assert "backup_verification" in report["hathi"]["missing_evidence"]
