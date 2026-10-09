"""Colonel Hathi must not infer verified backup or restore evidence."""
from mission_control.oap_data_hathi import StorageEvidence, hathi_assessment


def test_missing_recovery_evidence_is_not_green():
    report = hathi_assessment(StorageEvidence(True, False, False, True))
    assert report["ready"] is False
    assert report["missing_evidence"] == ["backup_verification", "restore_test"]
    assert report["destructive_actions_authorized"] is False


def test_all_evidence_still_requires_founder_final():
    report = hathi_assessment(StorageEvidence(True, True, True, True))
    assert report["ready"] is True
    assert report["founder_final_required"] is True
    assert report["destructive_actions_authorized"] is False
