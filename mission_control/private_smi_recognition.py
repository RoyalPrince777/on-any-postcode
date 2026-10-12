"""Founder-private SMI recognition policy: advisory only, fail closed.

This module deliberately does not capture sensors, identify a person, infer health,
or authorize any consequential action.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class EvidenceState(str, Enum):
    VERIFIED = "verified"
    ESTIMATED = "estimated"
    DISPUTED = "disputed"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class Observation:
    category: str
    source: str
    observed_at: str
    permission_granted: bool
    state: EvidenceState
    confidence: float
    value: str

    def __post_init__(self) -> None:
        if not 0 <= self.confidence <= 1:
            raise ValueError("confidence must be within [0, 1]")


SENSITIVE_CATEGORIES = frozenset({
    "health", "biometric", "legal", "location", "financial",
})


def project_observation(observation: Observation, *, founder_authenticated: bool) -> dict:
    """Never return personal data unless Founder authentication and consent hold."""
    if not founder_authenticated or not observation.permission_granted:
        return {"status": "DENIED", "value": None}
    return {
        "status": "ADVISORY_ONLY",
        "category": observation.category,
        "source": observation.source,
        "observed_at": observation.observed_at,
        "state": observation.state.value,
        "confidence": observation.confidence,
        "value": observation.value,
        "sensitive": observation.category in SENSITIVE_CATEGORIES,
        "identity_verified": False,
        "action_authorized": False,
    }


def recognition_authorizes_action(*, observation: Observation) -> bool:
    """Recognition never substitutes for authentication or human authority."""
    return False
