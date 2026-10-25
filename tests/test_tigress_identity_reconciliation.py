from mission_control.tigress_identity_reconciliation import (
    tigress_identity_reconciliation,
)


def test_tigress_review_does_not_reassign_tiger_identity():
    report = tigress_identity_reconciliation()
    assert report["mode"] == "read_only"
    assert report["preferred_name"] == "Tigress"
    assert report["tiger_agent_id"] == "ANIMAL-TIGER-001"
    assert report["shere_khan_agent_id"] == "JUNGLE-SHERE-KHAN-001"
    assert not report["identity_merge_approved"]
    assert not report["passport_verified"]
    assert not report["execution_authorised"]
    assert report["founder_final_required"]
    if not report["tigress_registered"]:
        assert report["tigress_agent_id"] is None
