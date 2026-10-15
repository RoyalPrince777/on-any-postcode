"""Bounded agent-role upgrade: evidence-driven advisory assignments only.

No worker execution, authority expansion, permission changes or fabricated votes.
"""
from __future__ import annotations

from dataclasses import dataclass

from oap.smi.alliance_assurance import AssuranceReview


@dataclass(frozen=True)
class SpecialistAssignment:
    specialist: str
    duty: str
    evidence_keys: tuple[str, ...]
    advisory_only: bool = True


def plan_assurance_specialists(review: AssuranceReview) -> tuple[SpecialistAssignment, ...]:
    """Assign distinct protection, recovery, verification and challenge duties."""
    issues = tuple(sorted(set(review.missing + review.contradictions)))
    assignments = [
        SpecialistAssignment("Gorilla", "Oversee defensive and recovery boundaries", issues),
        SpecialistAssignment("Tank", "Protect already verified requirements", review.observed),
        SpecialistAssignment("Dozer", "Resolve blockers without bypassing controls", issues),
        SpecialistAssignment("Twin One", "Define required acceptance evidence", review.expected),
        SpecialistAssignment("Twin Two", "Independently check actual evidence", issues),
        SpecialistAssignment("Agent Smith", "Challenge assumptions and unproven claims", issues),
    ]
    if review.contradictions:
        assignments.extend((
            SpecialistAssignment("Jones", "Investigate contradictory evidence", review.contradictions),
            SpecialistAssignment("Jackson", "Investigate anomalous observations", review.contradictions),
        ))
    if review.missing:
        assignments.extend((
            SpecialistAssignment("Brown", "Investigate repeated evidence gaps", review.missing),
            SpecialistAssignment("Thompson", "Challenge unsupported Green claims", review.missing),
        ))
    assignments.extend((
        SpecialistAssignment("Johnson", "Challenge resilience of verified conditions", review.observed),
        SpecialistAssignment("Shere Khan", "Adversarially review proof quality", review.expected),
    ))
    return tuple(assignments)
