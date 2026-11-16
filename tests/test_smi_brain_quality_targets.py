from mission_control import smi_brain_evidence_protocol as brain


def test_quality_targets_cover_exactly_the_14_canonical_regions():
    coverage = brain.validate_brain_quality_targets()
    assert coverage["passed"] is True
    assert coverage["regions_covered"] == 14
    assert coverage["regions_expected"] == 14
    assert coverage["runtime_metrics_verified"] is False
    assert coverage["promotion_authority"] is False


def test_quality_evidence_remains_unverified_without_runtime_proof():
    board = brain.evidence_gate_status()
    assert board["quality_coverage"]["passed"] is True
    assert len(board["brain_parts"]) == 14
    for region in board["brain_parts"]:
        assert region["quality_metric"]
        assert region["quality_acceptance"]
        assert region["quality_runtime_verified"] is False
        assert region["live_full_green"] is False
    assert board["live_full_green"] is False
    assert board["evidence_current"] == 42
    assert board["evidence_possible"] == 98
