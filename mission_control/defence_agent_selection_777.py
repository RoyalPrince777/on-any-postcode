"""Read-only defence specialist selection; no task execution or authority grants.

Selection only considers canonical registered agents, never suggested names.
An authenticated service must independently establish Founder/Guardian authority
before this projection is exposed or used.
"""
from __future__ import annotations

from . import agents, autonomy_levels
from .defensive_intelligence_777 import DIVISIONS

# Preferred role matches are advisory; never create a missing agent.
PREFERENCES = {
    "strategic": ("Lucy", "Morpheus", "Oracle"),
    "tactical": ("Tigress", "Bagheera", "Batman"),
    "earth_geoint": ("Nirmata", "Oracle"),
    "signals": ("Luther Stickell", "Benji Dunn"),
    "cyber": ("Benji Dunn", "Luther Stickell"),
    "human": ("Batman", "Grace", "Nyah Nordoff-Hall"),
    "counterintelligence": ("Shere Khan", "Bagheera", "Neo"),
}


def select_read_only(division: str, *, founder_verified: bool = False,
                     guardian_verified: bool = False) -> dict[str, object]:
    """Provide a bounded candidate list, never a live assignment."""
    if division not in DIVISIONS:
        raise ValueError("unknown division")
    if not founder_verified or not guardian_verified:
        raise PermissionError("authenticated Founder and Guardian decisions required")
    # A3/A4 capability evaluation is canonical; do not elevate levels.
    policy = autonomy_levels.evaluate_runtime_job("RUNTIME_HEALTH_PROBE")
    registry = {str(a.get("name", "")).casefold(): a for a in agents.AGENT_REGISTRY}
    candidates = []
    for name in PREFERENCES[division]:
        agent = registry.get(name.casefold())
        if not agent:
            continue
        # Registry membership alone does not establish a deployable passport.
        candidates.append({
            "name": agent["name"],
            "registry_status": agent.get("registry_status", "not_verified"),
            "passport_verified": False,
            "tools_authorised": False,
            "runtime_connected": False,
        })
    return {
        "division": division,
        "candidates": candidates,
        "canonical_autonomy_level": policy["configured_level"],
        "bounded_health_probe_policy_allowed": policy["allowed"],
        "selection_only": True,
        "assignment_active": False,
        "execution_granted": False,
        "human_authority_final": True,
        "hrm_receipt_persisted": False,
    }
