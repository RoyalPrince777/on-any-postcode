"""Contract tests for SMI capability/tool preflight."""

from oap.registry.tools import founder_tool_registry
from oap.smi.capability_preflight import preflight


def test_read_preflight_preserves_capability_selection() -> None:
    decision = preflight(
        founder_tool_registry(),
        task_type="TECHNICAL",
        query="review github code",
        tool_id="github",
        ability="repo.read",
    )
    assert decision.permitted_for_proposal
    assert "agentic_code_review" in decision.selected_capabilities
    assert decision.reason == "ALLOWLISTED_READ_PROPOSAL"


def test_mutation_remains_proposal_not_execution() -> None:
    decision = preflight(
        founder_tool_registry(),
        task_type="TECHNICAL",
        query="merge github PR",
        tool_id="github",
        ability="pr.merge",
        mutation=True,
    )
    assert decision.permitted_for_proposal
    assert decision.reason == "PROPOSAL_ONLY"
    assert decision.human_approval_required
    assert decision.kernel_required


def test_unknown_tool_fails_closed() -> None:
    decision = preflight(
        founder_tool_registry(),
        task_type="GENERAL",
        query="do something",
        tool_id="unknown",
        ability="anything",
    )
    assert not decision.permitted_for_proposal
    assert decision.reason == "DENIED_BY_REGISTRY"


def test_unknown_ability_fails_closed() -> None:
    decision = preflight(
        founder_tool_registry(),
        task_type="TECHNICAL",
        query="code",
        tool_id="github",
        ability="secrets.export",
    )
    assert not decision.permitted_for_proposal
