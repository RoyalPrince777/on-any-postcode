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
    execution_enabled: bool = False
    runtime_verified: bool = False

APPROVED_NINE = (
    "Genesis Sentinel", "Veritas", "Astraea", "Bastion", "Invictus",
    "Aeternum", "Omega Shield", "Obsidian Core", "Imperium Shield",
)
EARLIER_HISTORICAL = ("Eternalis", "Aurum Guard", "Celestia", "Titanis")
CAPABILITIES = tuple(
    AegisCapability(name, "approved_nine") for name in APPROVED_NINE
) + tuple(
    AegisCapability(name, "earlier_historical_unreconciled")
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
        "organ": "AEGIS",
        "approved_design_count": len(APPROVED_NINE),
        "unreconciled_historical_count": len(EARLIER_HISTORICAL),
        "runtime_verified_count": 0,
        "runtime_completion_percent": None,
        "execution_enabled": False,
    }
