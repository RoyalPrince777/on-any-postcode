"""MATRIX System routing and authority tests."""

import pytest

from mission_control.matrix_system import MISSION_TEAMS, SPECIALISTS, route_mission


@pytest.mark.parametrize("mission", tuple(MISSION_TEAMS))
def test_mission_routing_never_grants_execution_or_green(mission):
    result = route_mission(mission)
    assert result.specialists[:2] == ("fox", "octopus")
    assert all(agent in SPECIALISTS for agent in result.specialists)
    assert result.permitted_to_execute is False
    assert result.production_ready is False
    assert "human_authorisation_required" in result.blockers


def test_database_migration_requires_last_line_defence():
    assert "gorilla" in route_mission("database_migration").specialists


def test_distributed_work_includes_queen_bee_only_when_needed():
    assert "queen_bee" in route_mission("distributed_work").specialists
    assert "queen_bee" not in route_mission("public_endpoint").specialists


def test_unknown_mission_fails_closed():
    with pytest.raises(ValueError, match="unknown_matrix_mission"):
        route_mission("deploy_anything")


def test_evidence_is_not_equivalent_to_production_proof():
    result = route_mission("runtime_recovery", evidence=("CI passed",))
    assert result.evidence == ("CI passed",)
    assert result.production_ready is False


def test_invalid_evidence_rejected():
    with pytest.raises(ValueError, match="invalid_matrix_evidence"):
        route_mission("public_endpoint", evidence=("",))
