"""Canonical SMI auto-review routing and evidence vote board.

Named roles are deterministic review lenses. This module never claims that
fictional or simulated personalities independently thought or voted. Votes are
evidence classifications derived from the governed request state.
"""
from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any


ROLE_LENSES: tuple[tuple[str, tuple[str, ...], str], ...] = (
    ("Neo", ("neo",), "true path, execution coherence and recovery"),
    ("Shere Khan", ("shere khan", "claw test"), "adversarial stress, weakest link and survivability"),
    ("Bagheera", ("bagheera",), "protection, balance and reversible judgement"),
    ("Agent Smith", ("agent smith", "smith"), "duplication, corruption, bypass and false-green detection"),
    ("Morpheus", ("morpheus",), "mission clarity and alignment"),
    ("Trinity", ("trinity",), "integration and continuity"),
    ("Oracle", ("oracle",), "accuracy, uncertainty and adaptation"),
    ("Architect", ("architect",), "architecture, maintainability and dependency structure"),
    ("Keymaker", ("keymaker",), "access paths, routing and boundary integrity"),
    ("Seraph", ("seraph",), "security and alignment"),
    ("Owl", ("owl",), "evidence quality and wisdom"),
    ("Bee", ("bee",), "coordination and evidence gathering"),
    ("Elephant", ("elephant",), "memory, provenance and continuity"),
    ("Panther", ("panther",), "adaptation, gaps and security"),
    ("Eagle", ("eagle",), "whole-system view"),
    ("Falcon", ("falcon",), "speed and smallest bounded next gate"),
    ("Gorilla", ("gorilla",), "protection and pressure resistance"),
)

DEFAULT_AUTO_REVIEW = (
    "Neo",
    "Shere Khan",
    "Bagheera",
    "Agent Smith",
    "Owl",
    "Guardian",
    "Green Gate",
)


def explicit_roles(message: object) -> tuple[str, ...]:
    """Resolve Founder-typed names to canonical review lenses."""

    text = str(message or "").casefold()
    selected: list[str] = []
    for name, aliases, _ in ROLE_LENSES:
        if any(re.search(rf"(?<!\w){re.escape(alias)}(?!\w)", text) for alias in aliases):
            selected.append(name)
    return tuple(dict.fromkeys(selected))


def lens_for(name: str) -> str:
    for role_name, _, lens in ROLE_LENSES:
        if role_name == name:
            return lens
    return "governed evidence review"


def selected_roles(message: object, *, auto_mode: bool) -> tuple[str, ...]:
    explicit = explicit_roles(message)
    if explicit:
        return explicit
    if auto_mode:
        return DEFAULT_AUTO_REVIEW
    return ()


def _evidence_vote(
    *,
    passed: bool,
    blocked: bool,
    review_required: bool,
) -> str:
    if blocked:
        return "FAIL"
    if passed and not review_required:
        return "PASS"
    return "CONDITIONAL"


def build_vote_board(
    *,
    roles: tuple[str, ...],
    brain: Mapping[str, Any],
    coherence: Mapping[str, Any],
    judgement: Mapping[str, Any],
    guardian_outcome: str,
) -> dict[str, Any]:
    """Produce attributable deterministic evidence votes for the active roles."""

    if not roles:
        return {
            "automatic": False,
            "roles": (),
            "votes": (),
            "summary": {"PASS": 0, "FAIL": 0, "CONDITIONAL": 0},
            "authority_granted": False,
        }

    blocked = str(guardian_outcome).upper() == "BLOCKED"
    coherent = bool(coherence.get("passed"))
    constitution = bool(judgement.get("constitution_consistent"))
    provider_ready = bool(brain.get("passed"))
    high_impact = bool(brain.get("high_impact"))
    review_required = bool(
        not coherent
        or not constitution
        or high_impact
        or str(guardian_outcome).upper() == "REVIEW_REQUIRED"
    )
    base_vote = _evidence_vote(
        passed=bool(provider_ready and coherent and constitution),
        blocked=blocked,
        review_required=review_required,
    )

    votes = []
    for reviewer in roles:
        vote = base_vote
        reason = "Current governed evidence supports the recommendation."
        if reviewer == "Shere Khan" and (high_impact or not coherent):
            vote = "CONDITIONAL" if not blocked else "FAIL"
            reason = "Claw Test holds until survivability, weak-link and recovery evidence are strong."
        elif reviewer in {"Guardian", "Green Gate"}:
            if blocked:
                vote = "FAIL"
                reason = "Protection/evidence gate is blocked."
            elif review_required:
                vote = "CONDITIONAL"
                reason = "Protection/evidence gate requires further proof."
        elif reviewer == "Agent Smith" and not constitution:
            vote = "CONDITIONAL" if not blocked else "FAIL"
            reason = "Integrity review detected an unresolved governance/coherence condition."

        votes.append(
            {
                "reviewer": reviewer,
                "lens": lens_for(reviewer),
                "vote": vote,
                "reason": reason,
                "deterministic_evidence_review": True,
                "independent_personality_claimed": False,
            }
        )

    summary = {
        state: sum(1 for item in votes if item["vote"] == state)
        for state in ("PASS", "FAIL", "CONDITIONAL")
    }
    return {
        "automatic": True,
        "roles": roles,
        "votes": tuple(votes),
        "summary": summary,
        "authority_granted": False,
        "human_authority_final": True,
    }
