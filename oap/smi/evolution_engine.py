"""Learning proposals without autonomous self-modification."""

from __future__ import annotations

from collections.abc import Iterable
from uuid import uuid4

from oap.contracts import EvolutionProposal, KernelResult


class EvolutionEngine:
    def propose(self, outcomes: Iterable[KernelResult]) -> EvolutionProposal:
        records = tuple(outcomes)
        blocked = sum(not outcome.executed for outcome in records)
        evidence = (
            f"Reviewed outcomes: {len(records)}",
            f"Blocked outcomes: {blocked}",
        )
        return EvolutionProposal(
            proposal_id=str(uuid4()),
            title="Review SMI outcome patterns",
            description=(
                "Human Authority may review the evidence and approve a bounded "
                "refinement; no code, rule or permission changes automatically."
            ),
            evidence=evidence,
            requires_human_approval=True,
        )

    def apply(self, proposal: EvolutionProposal) -> None:
        del proposal
        raise PermissionError("Evolution proposals cannot self-apply")
