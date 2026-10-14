"""Alliance selection is deterministic and never an execution grant."""

from oap.smi.alliance_selection import select_alliance


def test_code_mission_selects_neo() -> None:
    result = select_alliance("TECHNICAL", "review github code")
    assert "Neo" in result.specialists
    assert result.advisory_only and result.founder_final


def test_no_queen_bee_without_distributed_work() -> None:
    result = select_alliance("TECHNICAL", "swarm parallel agents")
    assert "Queen Bee" not in result.specialists
    assert "scale_out_swarm" in result.unassigned_capabilities


def test_queen_bee_when_distributed_work_is_explicit() -> None:
    result = select_alliance(
        "TECHNICAL", "swarm parallel agents", distributed_work=True
    )
    assert "Queen Bee" in result.specialists


def test_shark_selected_for_emerging_risk_without_execution_authority() -> None:
    result = select_alliance("MONITORING", "shark emerging risk early warning")
    assert "Shark" in result.specialists
    assert "early_signal_detection" in result.capabilities
    assert result.advisory_only and result.founder_final


def test_shark_not_assigned_for_ordinary_code_review() -> None:
    result = select_alliance("TECHNICAL", "review github code")
    assert "Shark" not in result.specialists


def test_no_duplicated_specialists() -> None:
    result = select_alliance("TECHNICAL", "code review refactor test")
    assert len(result.specialists) == len(set(result.specialists))
