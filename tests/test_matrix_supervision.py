from __future__ import annotations

import pytest

from mission_control.matrix_supervision import supervision_snapshot


def test_no_runtime_evidence_does_not_claim_green() -> None:
    result = supervision_snapshot()
    assert set(result["identities"]) == {"Tank", "Dozer", "Link"}
    assert all(x["state"] == "not_connected" for x in result["identities"].values())
    assert result["full_green"] is False
    assert result["execution_granted"] is False
    assert result["delivery_confirmed"] is False
    assert result["recovery_verified"] is False


def test_supplied_evidence_does_not_grant_execution() -> None:
    result = supervision_snapshot({
        "Tank": {"state": "healthy", "evidence": "worker-check:123"},
        "Dozer": {"state": "failed", "evidence": "service-check:456"},
        "Link": {"state": "unknown", "evidence": "receipt-check:789"},
    })
    assert result["identities"]["Dozer"]["state"] == "failed"
    assert result["identities"]["Link"]["evidence"] == "receipt-check:789"
    assert result["all_clear_proven"] is False
    assert result["runtime_verified"] is False
    assert result["human_authority_final"] is True


@pytest.mark.parametrize("observations", [
    {"Unknown": {"state": "healthy", "evidence": "x"}},
    {"Tank": {"state": "healthy"}},
    {"Link": {"state": "up", "evidence": "x"}},
])
def test_invalid_observations_fail_closed(observations) -> None:
    with pytest.raises(ValueError):
        supervision_snapshot(observations)
