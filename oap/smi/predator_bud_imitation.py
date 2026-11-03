"""Bud imitation: verified-procedure reuse proposals, never automatic execution."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Procedure:
    identifier: str
    source: str
    steps: tuple[str, ...]
    outcome: str
    verified: bool


@dataclass(frozen=True)
class ImitationProposal:
    decision: str
    reason: str
    procedure_id: str
    steps: tuple[str, ...]
    executable: bool = False


def imitate(procedure: Procedure | None) -> ImitationProposal:
    """Copy steps only from explicitly verified, successful first-party records."""
    denied = ImitationProposal("DENY", "UNVERIFIED_PROCEDURE", "", ())
    if not isinstance(procedure, Procedure):
        return denied
    if not (
        procedure.verified is True
        and isinstance(procedure.identifier, str) and procedure.identifier.strip()
        and procedure.source == "first_party"
        and procedure.outcome == "success"
        and isinstance(procedure.steps, tuple)
        and bool(procedure.steps)
        and all(isinstance(step, str) and step.strip() for step in procedure.steps)
    ):
        return denied
    return ImitationProposal(
        "HUMAN_REVIEW", "VERIFIED_EXAMPLE_REQUIRES_AUTHORISATION",
        procedure.identifier, procedure.steps,
    )
