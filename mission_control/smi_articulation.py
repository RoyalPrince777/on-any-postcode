"""Advisory articulation plans for SMI communication, without action authority.

No audio processing, emotional inference, outbound communication or transactions.
"""
from __future__ import annotations

from dataclasses import dataclass

APPLICATIONS = frozenset({
    "founder", "customer_service", "sales", "negotiation",
    "agent", "voice", "emergency",
})
PRESSURE_MODES = frozenset({"normal", "challenged", "urgent"})


@dataclass(frozen=True)
class ArticulationPlan:
    application: str
    pressure_mode: str
    structure: tuple[str, ...]
    safeguards: tuple[str, ...]
    execution_class: str = "advisory"


def articulation_plan(
    application: str, pressure_mode: str = "normal", *, consent: bool = False
) -> ArticulationPlan:
    """Select communication structure; never infer pressure from a person."""
    if application not in APPLICATIONS:
        raise ValueError("Unknown articulation application")
    if pressure_mode not in PRESSURE_MODES:
        raise ValueError("Unknown pressure mode")
    if application == "voice" and not consent:
        raise PermissionError("Voice assistance requires explicit consent")
    if application == "emergency":
        structure = ("verified situation", "immediate safety instruction",
                     "confirmation", "human emergency escalation")
    elif application == "agent":
        structure = ("objective", "authority", "evidence", "uncertainty",
                     "requested advisory output", "verification")
    elif application in {"sales", "negotiation"}:
        structure = ("position", "verified facts", "options", "trade-offs",
                     "human decision")
    else:
        structure = ("main point", "supporting evidence", "clear conclusion")
    safeguards = (
        "Preserve the speaker's intended meaning",
        "Distinguish verified facts from uncertainty",
        "Never impersonate a person or infer hidden emotions",
        "No external actions, purchases, bookings or dispatch",
        "Human authority and Guardian permissions remain final",
    )
    if pressure_mode != "normal":
        structure = ("brief acknowledgement",) + structure
    return ArticulationPlan(application, pressure_mode, structure, safeguards)
