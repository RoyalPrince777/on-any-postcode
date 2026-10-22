"""Fox recovery intelligence: bounded, evidence-first recovery proposals only.

No route is changed, no service restarted, and no permission is granted here.
Fox remains in its canonical family; requesting families retain ownership.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FoxRecoveryRequest:
    mission_id: str
    requesting_family: str
    failure_kind: str
    observed_evidence: tuple[str, ...]
    approved_fallbacks: tuple[str, ...] = ()


@dataclass(frozen=True)
class FoxRecoveryPlan:
    mission_id: str
    requesting_family: str
    action: str
    selected_fallback: str | None
    evidence: tuple[str, ...]
    advisory_only: bool = True
    authority_granted: bool = False
    route_changed: bool = False
    runtime_verified: bool = False
    family_ownership_unchanged: bool = True


def propose_fox_recovery(request: FoxRecoveryRequest) -> FoxRecoveryPlan:
    """Fail closed without observed evidence or an explicitly approved fallback."""
    if not request.mission_id.strip() or not request.requesting_family.strip():
        raise ValueError("Mission and requesting family are required")
    if not request.failure_kind.strip():
        raise ValueError("Failure kind is required")
    evidence = tuple(e.strip() for e in request.observed_evidence if e.strip())
    fallback = next((f.strip() for f in request.approved_fallbacks if f.strip()), None)
    if not evidence:
        action = "hold_missing_evidence"
        fallback = None
    elif fallback is None:
        action = "hold_no_approved_fallback"
    else:
        action = "propose_approved_fallback_for_human_review"
    return FoxRecoveryPlan(
        request.mission_id, request.requesting_family, action, fallback, evidence
    )
