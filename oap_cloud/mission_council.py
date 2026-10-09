"""Evidence-aware advisory council for OAP missions; no autonomous voting implied."""
from collections import Counter

VALID_VOTES = frozenset({"FOR", "AGAINST", "ABSTAIN"})


def review_leadership(mission, candidates, ballots, evidence_gates):
    """Return a transparent recommendation, never an automatic promotion.

    Ballots are supplied by an authenticated orchestration layer, not generated
    or accepted from public HTTP requests. No candidate may vote for themselves.
    """
    if not isinstance(mission, str) or not mission.strip():
        raise ValueError("mission required")
    if not isinstance(candidates, dict) or not candidates:
        raise ValueError("candidates required")
    if not isinstance(evidence_gates, dict) or len(evidence_gates) != 10:
        raise ValueError("exactly ten evidence gates required")
    if any(type(v) is not bool for v in evidence_gates.values()):
        raise ValueError("evidence gates must be verified booleans")
    if any(not isinstance(k, str) or not k.strip() for k in evidence_gates):
        raise ValueError("invalid evidence gate")
    if not isinstance(ballots, list):
        raise ValueError("ballots required")
    tally = {candidate: Counter() for candidate in candidates}
    seen = set()
    dissent = []
    for ballot in ballots:
        if not isinstance(ballot, dict):
            raise ValueError("invalid ballot")
        voter, candidate, vote = (ballot.get(k) for k in ("voter", "candidate", "vote"))
        reason = ballot.get("reason")
        if not all(isinstance(v, str) and v.strip() for v in (voter, candidate, vote, reason)):
            raise ValueError("ballot must include identity and rationale")
        if candidate not in candidates or vote not in VALID_VOTES or voter == candidate:
            raise ValueError("invalid candidate, vote or self-vote")
        if (voter, candidate) in seen:
            raise ValueError("duplicate vote")
        seen.add((voter, candidate))
        tally[candidate][vote] += 1
        if vote != "FOR":
            dissent.append({"voter": voter, "candidate": candidate, "vote": vote, "reason": reason})
    for candidate, details in candidates.items():
        if not isinstance(candidate, str) or not candidate.strip() or not isinstance(details, dict):
            raise ValueError("invalid candidate")
        rating = details.get("rating")
        if rating is not None and (type(rating) is not int or not 1 <= rating <= 7):
            raise ValueError("rating must be 1..7 or unknown")
        if rating is not None and (not isinstance(details.get("evidence"), list) or not details["evidence"] or not all(isinstance(item, str) and item.strip() for item in details["evidence"])):
            raise ValueError("ratings require evidence")
    percentage = 10 * sum(evidence_gates.values())
    # Ten self-reported gates cannot independently certify a live deployment.\n    # The seventh star requires a separate, audited release certification.\n    stars = max(1, min(5, percentage // 20 + 1))
    return {
        "mission": mission, "mode": "recorded_advisory_ballots_not_autonomous_agents",
        "candidates": candidates,
        "votes": {c: {v: tally[c][v] for v in ("FOR", "AGAINST", "ABSTAIN")} for c in candidates},
        "dissent": dissent, "percentage": percentage, "mission_stars": stars,
        "leader": "pending_founder_final",
        "production_green": False,
        "release_certification": "not_verified",
    }
