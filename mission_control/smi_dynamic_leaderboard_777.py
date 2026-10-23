"""Evidence-based, non-executing dynamic intelligence leaderboard.

Rank is mission-relative and advisory. Membership and authority never change.
Unverified candidates remain unranked. No fictional votes or cosmetic scores.
"""
from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

CRITERIA = ("relevance", "verified_quality", "reliability", "collaboration", "safety")
WEIGHTS = {"relevance": 30, "verified_quality": 30, "reliability": 20,
           "collaboration": 10, "safety": 10}
AUTHORITY = ("Founder Final", "Guardian", "HRM")

def dynamic_leaderboard(
    mission: str,
    candidates: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    """Rank verified contributions only; never change operational permissions.

    Candidate contract: name, evidence_id, verified (literal True), and scores
    0..100 for every criterion. Scores must originate from a separate verified
    assessment; this pure function cannot validate external evidence itself.
    """
    if not isinstance(mission, str) or not mission.strip():
        raise ValueError("mission required")
    ranked: list[dict[str, Any]] = []
    unranked: list[dict[str, str]] = []
    seen: set[str] = set()
    for candidate in candidates:
        name = candidate.get("name")
        if not isinstance(name, str) or not name.strip() or name in seen:
            raise ValueError("candidate names must be unique nonempty strings")
        seen.add(name)
        evidence_id = candidate.get("evidence_id")
        scores = candidate.get("scores")
        if candidate.get("verified") is not True or not isinstance(evidence_id, str) or not evidence_id.strip():
            unranked.append({"name": name, "reason": "missing_verified_evidence"})
            continue
        if not isinstance(scores, Mapping) or set(scores) != set(CRITERIA) or any(
            isinstance(scores[k], bool) or not isinstance(scores[k], (int, float))
            or not 0 <= scores[k] <= 100 for k in CRITERIA
        ):
            unranked.append({"name": name, "reason": "missing_valid_assessment"})
            continue
        total = sum(float(scores[k]) * WEIGHTS[k] for k in CRITERIA) / 100
        ranked.append({"name": name, "score": round(total, 2),
                       "evidence_id": evidence_id, "authority_granted": False})
    ranked.sort(key=lambda r: (-r["score"], r["name"]))
    for position, candidate in enumerate(ranked, 1):
        candidate["position"] = position
    return {
        "mission": mission, "mode": "advisory_only", "authority": list(AUTHORITY),
        "no_agent_executed": True, "no_permission_changes": True,
        "ranked": ranked, "unranked": unranked,
        "overall_vpi": None, "evidence_externally_verified_by_this_module": False,
    }
