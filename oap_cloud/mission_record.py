"""Single structured mission record; no autonomous agents or deployment claims."""
from copy import deepcopy

from .mission_council import review_leadership


def build_mission_record(*, mission, candidates, ballots, evidence_gates,
                         done, next_actions, recovery, evidence_links, founder_decision="pending"):
    """Combine verifiable gates, advisory dissent and action state in one record."""
    if founder_decision not in {"pending", "approved", "rejected"}:
        raise ValueError("invalid Founder decision")
    for value in (done, next_actions, recovery, evidence_links):
        if not isinstance(value, list) or not all(isinstance(item, str) and item.strip() for item in value):
            raise ValueError("mission sections must contain valid text entries")
    council = review_leadership(mission, candidates, ballots, evidence_gates)
    # Approval is a recorded decision, not a security or deployment override.
    return {
        "schema": "oap.mission.v1",
        "mission": mission,
        "completion": {"percentage": council["percentage"], "stars": council["mission_stars"],
                       "gates": deepcopy(evidence_gates)},
        "leadership": {"proposed_candidates": deepcopy(candidates),
                       "selected_leader": "pending_verified_selection",
                       "captain": "ALL IN", "founder_final": founder_decision},
        "council": {"mode": council["mode"], "votes": council["votes"],
                    "dissent": council["dissent"]},
        "done": list(done), "next": list(next_actions), "recovery": list(recovery),
        "evidence_links": list(evidence_links),
        "production_green": council["production_green"] and founder_decision == "approved",
    }
