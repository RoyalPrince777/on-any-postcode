"""Universal SMI intelligence protocol: advisory records, no new agent registry.

Primary ownership does not exclude others from developing the same capability.
No autonomous learning, promotion, permission change, or production claims.
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from oap.smi.alliance_selection import _ROLE_CAPABILITIES

PROTOCOL = (
    "individual_identity", "shared_capability_access", "evidence_before_promotion",
    "mutual_teaching_with_attribution", "no_permanent_superiority",
    "one_existing_foundation", "guardian_and_founder_final",
)


def advisory_growth_record(*, agent: str, capability: str,
                           evidence: Mapping[str, Any],
                           shared_from: str | None = None) -> dict[str, Any]:
    """Create a fail-closed candidate record; never certify learning or ranking."""
    if not isinstance(agent, str) or not agent.strip():
        raise ValueError("agent required")
    if not isinstance(capability, str) or not capability.strip():
        raise ValueError("capability required")
    if not isinstance(evidence, Mapping):
        raise TypeError("evidence mapping required")
    if any(not isinstance(evidence.get(k), str) or not evidence[k].strip()
           for k in ("source", "reference", "observation")):
        raise ValueError("traceable evidence fields required")
    if shared_from is not None and (not isinstance(shared_from, str) or not shared_from.strip()):
        raise ValueError("shared_from must name a contributor")
    lead = next((name for name, capabilities in _ROLE_CAPABILITIES
                 if capability in capabilities), None)
    return {
        "agent": agent, "capability": capability,
        "accountable_lead": lead, "shared_from": shared_from,
        "evidence_reference": evidence["reference"],
        "evidence_verified": False, "learning_verified": False,
        "rank_change": None, "mode": "advisory",
        "guardian_review_required": True, "founder_final": True,
        "production_gate": "blocked",
    }
