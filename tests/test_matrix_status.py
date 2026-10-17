"""Read-only MATRIX status is consistent with the existing War Room truth boundary."""

import pytest

from mission_control.matrix_status import matrix_mission_status, matrix_registry_status


def test_registry_does_not_claim_live_agent_execution():
    status = matrix_registry_status()
    assert status["registered_passports"] >= 30
    assert len(status["modes"]) == 7
    assert len(status["ranks"]) == 7
    assert status["runtime_active"] is False
    assert status["execution_authorised"] is False
    assert status["production_ready"] is False


@pytest.mark.parametrize("mission", ("database_migration", "public_endpoint", "runtime_recovery", "distributed_work"))
def test_mission_status_keeps_captain_and_peers_without_green(mission):
    status = matrix_mission_status(mission)
    assert status["command"] == "smi"
    assert status["captain"] == "captain_all_in"
    assert status["coordinators"] == ("fox", "octopus")
    assert status["recommended_lead"]
    assert status["approved"] is False
    assert status["runtime_active"] is False
    assert status["production_ready"] is False


def test_status_rejects_unknown_mission():
    with pytest.raises(ValueError, match="unknown_matrix_mission"):
        matrix_mission_status("unbounded")
