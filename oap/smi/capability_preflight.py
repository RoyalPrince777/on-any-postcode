"""Fail-closed, side-effect-free preflight joining existing SMI and tool registries.

This module does not invoke tools, confer permissions or claim runtime parity.
"""

from __future__ import annotations

from dataclasses import dataclass

from oap.registry.tools import ToolRegistry
from oap.smi.capability_fabric import select_capabilities


@dataclass(frozen=True)
class CapabilityPreflight:
    selected_capabilities: tuple[str, ...]
    tool_id: str
    ability: str
    permitted_for_proposal: bool
    reason: str
    human_approval_required: bool
    kernel_required: bool


def preflight(
    registry: ToolRegistry,
    *,
    task_type: str,
    query: str,
    tool_id: str,
    ability: str,
    mutation: bool = False,
    high_impact: bool = False,
) -> CapabilityPreflight:
    """Return a bounded recommendation, never an execution grant."""
    selected = select_capabilities(task_type, query, high_impact=high_impact)
    try:
        tool = registry.authorize_capability(tool_id, ability, mutation=mutation)
    except (LookupError, PermissionError):
        return CapabilityPreflight(
            selected, tool_id, ability, False, "DENIED_BY_REGISTRY", True, True
        )
    return CapabilityPreflight(
        selected,
        tool.tool_id,
        ability,
        True,
        "PROPOSAL_ONLY" if mutation else "ALLOWLISTED_READ_PROPOSAL",
        tool.requires_human_approval,
        tool.requires_kernel,
    )
