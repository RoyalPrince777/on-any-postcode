"""Join existing Alliance recommendations to canonical tool preflight, without execution."""

from __future__ import annotations

from dataclasses import dataclass

from mission_control.oap_system_protocol import agent_handoff
from oap.registry.tools import ToolRegistry
from oap.smi.alliance_selection import AllianceSelection, select_alliance
from oap.smi.capability_preflight import CapabilityPreflight, preflight


@dataclass(frozen=True)
class GovernedAllianceProposal:
    alliance: AllianceSelection
    tool: CapabilityPreflight
    permitted_for_proposal: bool
    reason: str
    execution_authorised: bool = False


def propose_alliance_tool(
    registry: ToolRegistry,
    *,
    task_type: str,
    query: str,
    tool_id: str,
    ability: str,
    mutation: bool = False,
    high_impact: bool = False,
    distributed_work: bool = False,
) -> GovernedAllianceProposal:
    """Recommend specialists only when the existing registry permits a tool proposal.

    Does not grant an execution capability, start workers, or write HRM receipts.
    """
    alliance = select_alliance(
        task_type, query, high_impact=high_impact,
        distributed_work=distributed_work,
    )
    tool = preflight(
        registry, task_type=task_type, query=query, tool_id=tool_id,
        ability=ability, mutation=mutation, high_impact=high_impact,
    )
    if not tool.permitted_for_proposal:
        return GovernedAllianceProposal(
            alliance, tool, False, "DENIED_BY_REGISTRY",
        )
    return GovernedAllianceProposal(
        alliance, tool, True, tool.reason,
    )


def propose_alliance_handoff(
    proposal: GovernedAllianceProposal,
    *,
    requesting_agent: str,
    helping_agent: str,
    assignment: str,
    permitted_evidence: tuple[str, ...] = (),
) -> dict[str, object] | None:
    """Prepare an advisory handoff only after canonical proposal preflight.

    Never starts a worker, transfers authority, or writes an HRM receipt.
    """
    if not proposal.permitted_for_proposal:
        return None
    if helping_agent not in proposal.alliance.specialists:
        return None
    handoff = agent_handoff(
        requesting_agent, helping_agent, assignment,
        permitted_evidence=permitted_evidence,
    )
    return handoff if handoff["status"] == "READY" else None
