"""Join existing Alliance recommendations to canonical tool preflight, without execution."""

from __future__ import annotations

from dataclasses import dataclass

from oap.registry.tools import ToolRegistry
from oap.smi.alliance_selection import AllianceSelection, JungleMatrixSelection, select_alliance, select_jungle_matrix
from oap.smi.capability_preflight import CapabilityPreflight, preflight


@dataclass(frozen=True)
class GovernedAllianceProposal:
    alliance: AllianceSelection
    tool: CapabilityPreflight
    permitted_for_proposal: bool
    reason: str
    execution_authorised: bool = False
    jungle_matrix: JungleMatrixSelection | None = None


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
    jungle_matrix_review: bool = False,
) -> GovernedAllianceProposal:
    """Recommend specialists only when the existing registry permits a tool proposal.

    Does not grant an execution capability, start workers, or write HRM receipts.
    """
    alliance = select_alliance(
        task_type, query, high_impact=high_impact,
        distributed_work=distributed_work,
    )
    jungle_matrix = select_jungle_matrix(query) if jungle_matrix_review else None
    tool = preflight(
        registry, task_type=task_type, query=query, tool_id=tool_id,
        ability=ability, mutation=mutation, high_impact=high_impact,
    )
    if not tool.permitted_for_proposal:
        return GovernedAllianceProposal(
            alliance, tool, False, "DENIED_BY_REGISTRY", jungle_matrix=jungle_matrix,
        )
    return GovernedAllianceProposal(
        alliance, tool, True, tool.reason, jungle_matrix=jungle_matrix,
    )
