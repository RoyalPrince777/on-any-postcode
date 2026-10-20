"""Earth Is Our Turf: seven governed SMI responsibilities, not independent agents.

Definitions are advisory only. No source collection, publication, monitoring,
location access, or autonomous execution is authorised by this registry.
"""
from __future__ import annotations

from dataclasses import dataclass

@dataclass(frozen=True)
class EarthCapability:
    key: str
    label: str
    purpose: str
    source_required: bool = True
    human_publication_review: bool = True
    permission_required: bool = True
    personal_profiling_allowed: bool = False
    autonomous_execution_allowed: bool = False
    implementation_status: str = "NOT_VERIFIED"


_CAPABILITIES: tuple[EarthCapability, ...] = (
    EarthCapability("earth_pulse", "Earth Pulse", "Source-backed global civic and humanitarian events"),
    EarthCapability("any_postcode", "Any Postcode Intelligence", "Privacy-aware Earth-to-postcode geography"),
    EarthCapability("accountability", "Accountability Lens", "Public decisions and documented outcomes"),
    EarthCapability("rights", "Rights & Freedom Monitor", "Legal protections and official civic guidance"),
    EarthCapability("resilience", "Planetary Resilience", "Environmental and emergency information"),
    EarthCapability("opportunity", "Community Opportunity", "Verified public local services and opportunities"),
    EarthCapability("earth_memory", "Earth Memory", "Sourced timelines, corrections and retention"),
)
CAPABILITY_KEYS = tuple(item.key for item in _CAPABILITIES)
_BY_KEY = {item.key: item for item in _CAPABILITIES}


def list_earth_capabilities() -> tuple[EarthCapability, ...]:
    """Describe all seven responsibilities; does not claim they are operational."""
    return _CAPABILITIES


def get_earth_capability(key: object) -> EarthCapability | None:
    """Unknown or malformed capabilities have no fallback and no authority."""
    if not isinstance(key, str):
        return None
    return _BY_KEY.get(key.strip().lower())


def capability_publication_eligible(
    key: object, *, sources_verified: bool = False,
    permission_verified: bool = False, human_review_approved: bool = False,
) -> bool:
    """Fail closed: registry presence never constitutes permission to publish."""
    capability = get_earth_capability(key)
    return bool(
        capability is not None
        and capability.implementation_status == "VERIFIED"
        and sources_verified is True
        and permission_verified is True
        and human_review_approved is True
    )
