"""Read-only Tigress identity reconciliation; never assign an inferred passport ID."""
from __future__ import annotations

from .agents import AGENT_REGISTRY


def tigress_identity_reconciliation() -> dict:
    by_name = {str(a["name"]).casefold(): a for a in AGENT_REGISTRY}
    tiger = by_name.get("tiger")
    shere_khan = by_name.get("shere khan")
    tigress = by_name.get("tigress")
    return {
        "mode": "read_only",
        "preferred_name": "Tigress",
        "historical_spelling": "Tygress",
        "historical_role": "Precision / Discipline Intelligence",
        "tigress_registered": tigress is not None,
        "tigress_agent_id": tigress["agent_id"] if tigress else None,
        "tiger_agent_id": tiger["agent_id"] if tiger else None,
        "shere_khan_agent_id": shere_khan["agent_id"] if shere_khan else None,
        "identity_merge_approved": False,
        "passport_verified": False,
        "founder_final_required": True,
        "execution_authorised": False,
    }
