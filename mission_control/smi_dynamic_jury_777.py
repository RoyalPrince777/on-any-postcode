"""OAP Court 777: evidence-bound dynamic seven-seat jury selector.

Advisory only: this module does not appoint jurors, conduct proceedings,
make findings, or grant any execution or legal authority.
"""
from __future__ import annotations

JURY_SIZE = 7
FOUNDING_JURY = (
    ("Gyata", ("leadership", "governance")),
    ("Trinity", ("technical", "data", "security")),
    ("Bagheera", ("rights", "privacy", "defence")),
    ("Akela", ("accountability", "governance")),
    ("Owl", ("legal", "tax", "treaties")),
    ("Octopus", ("investigation", "fraud", "technical")),
    ("Esono", ("records", "history", "legal")),
)

def founding_candidates():
    return tuple({"id": name, "expertise": areas, "verified": False,
                  "independent": False, "conflicts_checked": False}
                 for name, areas in FOUNDING_JURY)

def recommend_jury(case, candidates):
    """Rank only verified, independently cleared candidates; fail closed.

    case requires a case_id, topics and excluded_agent_ids.
    Each candidate must provide an id, expertise, verified, independent,
    conflicts_checked, and conflict_free. No model-inferred clearance.
    """
    if not isinstance(case, dict) or not case.get("case_id"):
        return {"ready": False, "reason": "case_id_required", "jurors": ()}
    topics = case.get("topics", ())
    excluded = case.get("excluded_agent_ids", ())
    if (not isinstance(topics, (tuple, list)) or not topics or
        not all(isinstance(x, str) and x for x in topics) or
        not isinstance(excluded, (tuple, list, set))):
        return {"ready": False, "reason": "invalid_case_context", "jurors": ()}
    excluded = set(excluded)
    eligible = []
    seen = set()
    for agent in candidates:
        if not isinstance(agent, dict):
            continue
        aid = agent.get("id")
        if not isinstance(aid, str) or not aid or aid in seen:
            continue
        seen.add(aid)
        if aid in excluded or not all(agent.get(k) is True for k in (
            "verified", "independent", "conflicts_checked", "conflict_free")):
            continue
        expertise = agent.get("expertise", ())
        if not isinstance(expertise, (list, tuple, set)):
            continue
        score = len(set(topics).intersection(expertise))
        if score:
            eligible.append((score, aid))
    eligible.sort(key=lambda item: (-item[0], item[1]))
    if len(eligible) < JURY_SIZE:
        return {"ready": False, "reason": "insufficient_independent_jurors",
                "eligible_count": len(eligible), "jurors": ()}
    return {"ready": True, "reason": "advisory_selection_only",
            "jurors": tuple(aid for _, aid in eligible[:JURY_SIZE]),
            "requires_founder_approval": True, "appointments_executed": False}
