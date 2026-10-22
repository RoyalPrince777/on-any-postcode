"""Read-only AEGIS heritage inventory; not an agent registry or permission grant.

The nine active-design labels and four earlier historical labels are preserved
without claiming that any named capability has a runtime implementation.
AEGIS is the parent organ, not a fourteenth sub-agent.
"""
from __future__ import annotations

from dataclasses import dataclass

@dataclass(frozen=True)
class AegisCapability:
    name: str
    lineage: str
    proposed_responsibility: str = ""
    execution_enabled: bool = False
    runtime_verified: bool = False

APPROVED_NINE = (
    "Genesis Sentinel", "Veritas", "Astraea", "Bastion", "Invictus",
    "Aeternum", "Omega Shield", "Obsidian Core", "Imperium Shield",
)
EARLIER_HISTORICAL = ("Eternalis", "Aurum Guard", "Celestia", "Titanis")
PROPOSED_RESPONSIBILITIES = {
    "Genesis Sentinel": "Early warning and anomaly triage",
    "Veritas": "Evidence provenance and contradiction review",
    "Astraea": "Rule consistency and proportionality review",
    "Bastion": "Containment and isolation recommendations",
    "Invictus": "Resilience under failures and attacks",
    "Aeternum": "Continuity and preservation review",
    "Omega Shield": "Critical-system emergency restriction review",
    "Obsidian Core": "Internal integrity and trust boundary review",
    "Imperium Shield": "Governance and authorization safeguards",
    "Eternalis": "Long-term protection policy continuity",
    "Aurum Guard": "Financial and transaction risk review",
    "Celestia": "Environmental and infrastructure risk awareness",
    "Titanis": "Infrastructure hardening and defensive capacity"
}

PARENT_ORGAN = "AEGIS"
PARENT_RESPONSIBILITY = "Coordinate deterministic protection findings; Guardian retains authorization"

CAPABILITIES = tuple(
    AegisCapability(name, "approved_nine", PROPOSED_RESPONSIBILITIES[name]) for name in APPROVED_NINE
) + tuple(
    AegisCapability(name, "earlier_historical_unreconciled", PROPOSED_RESPONSIBILITIES[name])
    for name in EARLIER_HISTORICAL
)

def get_capability(name: str) -> AegisCapability | None:
    """Exact-name lookup; unknown names never receive authority."""
    if not isinstance(name, str):
        return None
    return next((item for item in CAPABILITIES if item.name == name), None)

def inventory_status() -> dict[str, object]:
    """Counts are design-inventory coverage, never completion percentages."""
    return {
        "organ": PARENT_ORGAN,
        "historical_named_components": 1 + len(CAPABILITIES),
        "responsibilities_are_proposals": True,
        "approved_design_count": len(APPROVED_NINE),
        "unreconciled_historical_count": len(EARLIER_HISTORICAL),
        "runtime_verified_count": 0,
        "runtime_completion_percent": None,
        "execution_enabled": False,
    }
