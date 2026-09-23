"""Read-only War Room front summary, separate from portfolio evidence and live votes.

No receipt writes, autonomous agent claims, execution permission or certification.
The canonical rule-lens registry is a capability inventory, not a mission review.
"""
from __future__ import annotations

from typing import Any, Mapping

from . import smi_judge_rotation

SIGNAL_DENOMINATOR = 21
STAR_DENOMINATOR = 7


def front_review_projection(
    judge_status: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Project existing registry facts without manufacturing run-specific proof."""
    status = judge_status if judge_status is not None else smi_judge_rotation.status()
    names = status.get("canonical_judges")
    count = status.get("canonical_count")
    complete = (
        status.get("all_judges_present") is True
        and isinstance(names, (tuple, list))
        and len(names) == STAR_DENOMINATOR
        and len(set(names)) == STAR_DENOMINATOR
        and type(count) is int
        and count == STAR_DENOMINATOR
    )
    return {
        "rule_lenses_registered": STAR_DENOMINATOR if complete else None,
        "rule_lens_denominator": STAR_DENOMINATOR,
        "rule_lens_mode": "bounded_rule_lens",
        "actual_vote_count": None,
        "actual_vote_denominator": None,
        "simulated_vote_count": None,
        "mission_stars_certified": None,
        "star_denominator": STAR_DENOMINATOR,
        "mission_signals_proven": None,
        "signal_denominator": SIGNAL_DENOMINATOR,
        "decision_debt_count": None,
        "recovery_gate_proven": None,
        "runtime_guard_proven": None,
        "aegis_proven": None,
        "founder_final_proven": None,
        "truth_boundary": (
            "Registered rule lenses are not genuine independent agent votes; "
            "missing mission evidence is unassessed, not zero failed checks."
        ),
    }
