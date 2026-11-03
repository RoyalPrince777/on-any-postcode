"""OAP 777 advisory merit ladder. No authority or promotions are granted here."""
from __future__ import annotations

from collections.abc import Mapping
from math import isfinite
from typing import Any

WEIGHTS = {
    "mission_results": 30, "continuity": 20, "safety": 20,
    "collaboration": 15, "innovation": 10, "peer_review": 5,
}
LADDER = (
    (98, "777 Grandmaster"), (94, "General"), (88, "Commander"),
    (80, "Captain"), (70, "Lieutenant"), (60, "Sergeant"), (0, "Scout"),
)

def assess_merit(
    scores: Mapping[str, int | float],
    *,
    evidence_receipts: tuple[str, ...] = (),
    safety_cleared: bool = False,
    independent_review_cleared: bool = False,
    peer_reviews: tuple[Mapping[str, Any], ...] = (),
    candidate_id: str = "",
) -> dict[str, Any]:
    """Compute a suggested band only after validated inputs; never issue badges.

    Receipt presence is not proof of authenticity. External HRM verification is
    required before any real promotion; this function is advisory-only.
    """
    if set(scores) != set(WEIGHTS) or any(
        isinstance(scores[k], bool) or not isinstance(scores[k], (int, float))
        or not isfinite(scores[k]) or not 0 <= scores[k] <= 100 for k in WEIGHTS
    ):
        raise ValueError("all six bounded merit scores required")
    score = round(sum(float(scores[k]) * WEIGHTS[k] for k in WEIGHTS) / 100, 2)
    band = next(name for threshold, name in LADDER if score >= threshold)
    reviews_ok = len(peer_reviews) == 7 and len({
        review.get("reviewer_id") for review in peer_reviews
        if isinstance(review.get("reviewer_id"), str) and review.get("reviewer_id")
    }) == 7 and all(
        review.get("reviewer_id") != candidate_id
        and review.get("independent") is True
        and review.get("conflict_of_interest") is False
        for review in peer_reviews
    )
    complete = bool(evidence_receipts) and safety_cleared and independent_review_cleared and reviews_ok
    return {
        "score": score, "proposed_band": band,
        "decision": "ELIGIBLE_FOR_HRM_VERIFICATION" if complete else "HOLD",
        "badge_issued": False, "authority_granted": False,
        "receipt_authenticity_verified": False,
        "missing": [
            key for key, ok in (
                ("evidence_receipts", bool(evidence_receipts)),
                ("safety_clearance", safety_cleared),
                ("independent_review", independent_review_cleared),
                ("seven_conflict_free_reviews", reviews_ok),
            ) if not ok
        ],
    }
