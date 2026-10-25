"""Read-only evidence report for SMI passport reconciliation.

Registry membership is distinct from Founder approval and runtime activation.
No changes to the locked canonical agent registry are made here.
"""
from __future__ import annotations

from . import agents

REVIEW_NAMES = ("Gorilla", "Fox", "Baloo", "Mouse", "Secretary", "Tigress", "Lioness")


def registry_passport_gap_report() -> dict:
    registered = {str(item["name"]).casefold(): item for item in agents.AGENT_REGISTRY}
    entries = []
    for name in REVIEW_NAMES:
        record = registered.get(name.casefold())
        entries.append({
            "name": name,
            "registered": record is not None,
            "agent_id": record["agent_id"] if record else None,
            "family_id": record["family_id"] if record else None,
            "passport_verified": False,
            "runtime_verified": False,
        })
    return {
        "mode": "read_only",
        "registry_count": len(agents.AGENT_REGISTRY),
        "registry_target": agents.LOCKED_AGENT_COUNT,
        "entries": entries,
        "founder_final_required": True,
        "execution_authorised": False,
    }
