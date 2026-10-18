"""Predator-inspired advisory role definitions; no agents or execution grants.

These fictional labels describe bounded research responsibilities only.
No sensor, tracking, identification or incident claim is established here.
"""
from dataclasses import dataclass

@dataclass(frozen=True)
class PredatorRole:
    role_id: str
    purpose: str
    execution_class: str = "advisory"
    sensor_connected: bool = False

ROLES: tuple[PredatorRole, ...] = (
    PredatorRole("jungle_hunter", "Review consented environmental observations."),
    PredatorRole("city_hunter", "Review existing urban mapping diagnostics."),
    PredatorRole("wolf", "Recommend incident containment for human review."),
    PredatorRole("feral_predator", "Assess resilience evidence and unknowns."),
    PredatorRole("scar", "Recommend coordination without dispatch authority."),
    PredatorRole("berserker", "Design defensive tests without executing them."),
    PredatorRole("tracker", "Trace provenance of authorised anomaly evidence."),
)

def role(role_id: str) -> PredatorRole | None:
    """Look up an exact, canonical role ID without side effects."""
    return next((item for item in ROLES if item.role_id == role_id), None)
