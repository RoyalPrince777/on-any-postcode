"""Contract tests: Alliance selection never weakens canonical tool permission gates."""

from oap.registry.tools import founder_tool_registry
from oap.smi.alliance_tool_proposal import propose_alliance_tool, propose_alliance_handoff


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


def test_allowed_proposal_produces_advisory_handoff_only() -> None:
    proposal = propose_alliance_tool(
        founder_tool_registry(), task_type="TECHNICAL",
        query="review github code", tool_id="github", ability="repo.read",
    )
    handoff = propose_alliance_handoff(
        proposal, requesting_agent="Octopus", helping_agent="Neo",
        assignment="review code", permitted_evidence=("source",),
    )
    assert handoff is not None
    assert handoff["status"] == "READY"
    assert handoff["authority_transferred"] is False
    assert handoff["hrm_receipt_required"] is True
    assert handoff["permitted_evidence"] == ("source",)
    assert not proposal.execution_authorised


def test_denied_proposal_cannot_create_handoff() -> None:
    proposal = propose_alliance_tool(
        founder_tool_registry(), task_type="TECHNICAL",
        query="review github code", tool_id="github", ability="secrets.export",
    )
    assert propose_alliance_handoff(
        proposal, requesting_agent="Octopus", helping_agent="Neo",
        assignment="export secrets",
    ) is None


def test_unselected_or_empty_handoff_fails_closed() -> None:
    proposal = propose_alliance_tool(
        founder_tool_registry(), task_type="TECHNICAL",
        query="review github code", tool_id="github", ability="repo.read",
    )
    assert propose_alliance_handoff(
        proposal, requesting_agent="Octopus", helping_agent="Queen Bee",
        assignment="start swarm",
    ) is None
    assert propose_alliance_handoff(
        proposal, requesting_agent="Octopus", helping_agent="Neo",
        assignment="",
    ) is None
