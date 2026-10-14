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


from oap.smi.alliance_selection import select_jungle_matrix


def test_jungle_matrix_selects_only_relevant_film_roles() -> None:
    result = select_jungle_matrix("Akela pack discipline with Bagheera jungle boundaries")
    assert result.jungle_roles == ("Akela", "Bagheera")
    assert result.matrix_reviewers == ()
    assert result.advisory_only and result.founder_final


def test_matrix_reviewers_are_bounded_and_not_automatic() -> None:
    result = select_jungle_matrix("Baloo practical learning; security privacy and edge case review", reviewer_limit=2)
    assert result.jungle_roles == ("Baloo",)
    assert result.matrix_reviewers == ("Morpheus", "Seraph")
    assert "Shark" not in result.jungle_roles


def test_empty_jungle_request_never_spawns_a_council() -> None:
    result = select_jungle_matrix("ordinary unrelated request")
    assert result.jungle_roles == ()
    assert result.matrix_reviewers == ()


def test_matrix_mouse_selected_when_reviewer_budget_allows() -> None:
    result = select_jungle_matrix("Baloo edge case", reviewer_limit=3)
    assert result.matrix_reviewers == ("Mouse",)


def test_matrix_zero_reviewer_budget() -> None:
    result = select_jungle_matrix("Bagheera security", reviewer_limit=0)
    assert result.jungle_roles == ("Bagheera",)
    assert result.matrix_reviewers == ()
