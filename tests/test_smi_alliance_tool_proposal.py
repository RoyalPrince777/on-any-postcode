"""Contract tests: Alliance selection never weakens canonical tool permission gates."""

from oap.registry.tools import founder_tool_registry
from oap.smi.alliance_tool_proposal import propose_alliance_tool


def test_allowed_read_is_only_proposal() -> None:
    result = propose_alliance_tool(
        founder_tool_registry(), task_type="TECHNICAL",
        query="review github code", tool_id="github", ability="repo.read",
    )
    assert result.permitted_for_proposal
    assert "Neo" in result.alliance.specialists
    assert not result.execution_authorised


def test_unknown_ability_fails_closed_even_with_specialists() -> None:
    result = propose_alliance_tool(
        founder_tool_registry(), task_type="TECHNICAL",
        query="review github code", tool_id="github", ability="secrets.export",
    )
    assert not result.permitted_for_proposal
    assert result.reason == "DENIED_BY_REGISTRY"
    assert not result.execution_authorised


def test_mutation_retains_human_and_kernel_gates() -> None:
    result = propose_alliance_tool(
        founder_tool_registry(), task_type="TECHNICAL",
        query="merge github PR", tool_id="github", ability="pr.merge",
        mutation=True,
    )
    assert result.permitted_for_proposal
    assert result.tool.human_approval_required
    assert result.tool.kernel_required
    assert not result.execution_authorised


def test_distributed_flag_does_not_override_denial() -> None:
    result = propose_alliance_tool(
        founder_tool_registry(), task_type="TECHNICAL",
        query="swarm parallel agents", tool_id="unknown", ability="run",
        distributed_work=True,
    )
    assert "Queen Bee" in result.alliance.specialists
    assert not result.permitted_for_proposal
    assert not result.execution_authorised


def test_jungle_matrix_opt_in_allowed_read_is_advisory() -> None:
    result = propose_alliance_tool(
        founder_tool_registry(), task_type="TECHNICAL",
        query="Baloo practical learning security review",
        tool_id="github", ability="repo.read", jungle_matrix_review=True,
    )
    assert result.permitted_for_proposal
    assert result.jungle_matrix is not None
    assert result.jungle_matrix.jungle_roles == ("Baloo",)
    assert "Seraph" in result.jungle_matrix.matrix_reviewers
    assert result.jungle_matrix.advisory_only and result.jungle_matrix.founder_final
    assert not result.execution_authorised


def test_jungle_matrix_opt_in_denied_ability_remains_denied() -> None:
    result = propose_alliance_tool(
        founder_tool_registry(), task_type="TECHNICAL",
        query="Akela security review", tool_id="github",
        ability="secrets.export", jungle_matrix_review=True,
    )
    assert result.jungle_matrix is not None
    assert "Akela" in result.jungle_matrix.jungle_roles
    assert not result.permitted_for_proposal
    assert result.reason == "DENIED_BY_REGISTRY"
    assert not result.execution_authorised


def test_jungle_matrix_default_does_not_change_existing_callers() -> None:
    result = propose_alliance_tool(
        founder_tool_registry(), task_type="TECHNICAL",
        query="Baloo", tool_id="github", ability="repo.read",
    )
    assert result.jungle_matrix is None
    assert not result.execution_authorised
