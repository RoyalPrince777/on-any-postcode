"""Raffles BODY: bounded, review-only command routing; no new Matrix or payment engine."""
from __future__ import annotations

from dataclasses import dataclass

from oap.raffles_control import RafflesControl
from oap.raffles_mind import MindResult, Triage

ALLOWED = frozenset({"REVIEW", "STOP", "RECOVER", "APPROVE_FOR_REVIEW"})
BLOCKED = frozenset({"OPEN_ENTRIES", "TAKE_PAYMENT", "SELECT_WINNER",
                     "PUBLISH", "DELIVER_PRIZE", "SEND_MARKETING"})

@dataclass(frozen=True)
class BodyOutcome:
    action: str
    outcome: str
    execution_granted: bool = False
    published: bool = False


def dispatch(control: RafflesControl, *, action: str, actor: str,
             mind: MindResult | None = None) -> BodyOutcome:
    """Return actual kernel acknowledgement; never invent successful UI receipts."""
    if action in BLOCKED:
        return BodyOutcome(action, "BLOCKED_RELEASE_SCOPE")
    if action not in ALLOWED:
        return BodyOutcome(action, "BLOCKED_UNKNOWN_ACTION")
    if action == "APPROVE_FOR_REVIEW" and (
        mind is None or mind.decision != Triage.ESCALATE
    ):
        return BodyOutcome(action, "BLOCKED_MIND_NOT_READY")
    result = control.control(action, actor)
    return BodyOutcome(action, result["outcome"])
