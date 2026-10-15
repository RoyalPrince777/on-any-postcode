"""Read-only identity enrichment of canonical Alliance selections.

Never changes specialist selection, tool permissions, or execution authority.
"""
from __future__ import annotations

from dataclasses import dataclass

from oap.smi.alliance_identity import AllianceIdentity, get_alliance_identity
from oap.smi.alliance_selection import AllianceSelection, select_alliance


@dataclass(frozen=True)
class IdentifiedSpecialist:
    name: str
    identity: AllianceIdentity | None


@dataclass(frozen=True)
class IdentifiedAlliance:
    selection: AllianceSelection
    specialists: tuple[IdentifiedSpecialist, ...]


def describe_alliance(selection: AllianceSelection) -> IdentifiedAlliance:
    """Enrich selected specialists without modifying their canonical selection."""
    specialists = tuple(
        IdentifiedSpecialist(
            name=name,
            identity=get_alliance_identity(name.lower().replace(" ", "_").replace("-", "_")),
        )
        for name in selection.specialists
    )
    return IdentifiedAlliance(selection=selection, specialists=specialists)


def select_identified_alliance(
    task_type: str,
    query: str,
    *,
    high_impact: bool = False,
    distributed_work: bool = False,
    limit: int = 8,
) -> IdentifiedAlliance:
    """Existing selection first; metadata second. No agent execution."""
    return describe_alliance(
        select_alliance(
            task_type,
            query,
            high_impact=high_impact,
            distributed_work=distributed_work,
            limit=limit,
        )
    )
