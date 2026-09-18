"""Upgrade-only War Room judge selection and performance ranking.

The stable review core is preserved. Registered specialist judges rotate by
task fit and evidence-backed performance. Rankings are advisory and never
grant authority, execution rights, or permission changes.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

STABLE_REVIEW_CORE = (
    "SMI First Look",
    "Shere Khan",
    "Bagheera",
    "Guardian",
    "Green Gate",
    "SMI Second Look",
    "Founder Final",
)

ROTATING_JUDGE_NAMES = (
    "Neo",
    "Gyata",
    "Akela",
    "Morpheus",
    "Oracle",
    "Architect",
    "Keymaker",
    "Seraph",
    "Agent Smith",
    "Owl",
)

SCORE_WEIGHTS = {
    "task_fit": 0.35,
    "evidence_quality": 0.20,
    "outcome_accuracy": 0.15,
    "useful_dissent": 0.10,
    "consistency": 0.10,
    "recent_performance": 0.10,
}

PERFORMANCE_TIERS = (
    (90, "Prime"),
    (80, "Core"),
    (70, "Specialist"),
    (60, "Supporting"),
    (0, "Probation"),
)


def _clamp(value: object) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return 0.0
    return max(0.0, min(100.0, number))


def _tier(score: float) -> str:
    for floor, name in PERFORMANCE_TIERS:
        if score >= floor:
            return name
    return "Probation"


def score_agent(
    metrics: Mapping[str, object],
    *,
    founder_correction_penalty: float = 0.0,
    missed_risk_penalty: float = 0.0,
    false_positive_penalty: float = 0.0,
) -> dict[str, Any]:
    """Score one agent without turning the result into authority."""

    parts = {
        key: _clamp(metrics.get(key))
        for key in SCORE_WEIGHTS
    }
    weighted = sum(parts[key] * weight for key, weight in SCORE_WEIGHTS.items())
    penalties = (
        _clamp(founder_correction_penalty)
        + _clamp(missed_risk_penalty)
        + _clamp(false_positive_penalty)
    )
    score = max(0.0, min(100.0, weighted - penalties))
    return {
        "score": round(score, 1),
        "tier": _tier(score),
        "metrics": parts,
        "penalties": {
            "founder_correction": _clamp(founder_correction_penalty),
            "missed_risk": _clamp(missed_risk_penalty),
            "false_positive": _clamp(false_positive_penalty),
        },
        "authority_effect": "none",
    }


def select_rotating_judges(
    candidates: Iterable[Mapping[str, Any]],
    *,
    task_domains: Iterable[str],
    depth: int = 7,
    challenger_slot: bool = True,
) -> dict[str, Any]:
    """Select registered rotating judges while preserving the locked core.

    Candidates must be registered/active and supply per-domain suitability plus
    evidence-backed performance metrics. Unknown/unregistered names are ignored.
    """

    domain_set = {str(item).strip().casefold() for item in task_domains if str(item).strip()}
    scored: list[dict[str, Any]] = []

    for candidate in candidates:
        name = str(candidate.get("name") or "").strip()
        if name not in ROTATING_JUDGE_NAMES:
            continue
        if str(candidate.get("registry_status") or "").upper() != "ACTIVE":
            continue

        domain_scores = candidate.get("domain_scores")
        if not isinstance(domain_scores, Mapping):
            domain_scores = {}
        relevant = [
            _clamp(value)
            for key, value in domain_scores.items()
            if str(key).casefold() in domain_set
        ]
        task_fit = max(relevant) if relevant else _clamp(candidate.get("task_fit"))

        metrics = candidate.get("performance")
        if not isinstance(metrics, Mapping):
            metrics = {}
        merged_metrics = dict(metrics)
        merged_metrics["task_fit"] = task_fit

        score = score_agent(
            merged_metrics,
            founder_correction_penalty=_clamp(candidate.get("founder_correction_penalty")),
            missed_risk_penalty=_clamp(candidate.get("missed_risk_penalty")),
            false_positive_penalty=_clamp(candidate.get("false_positive_penalty")),
        )
        scored.append(
            {
                "name": name,
                "score": score["score"],
                "tier": score["tier"],
                "task_fit": task_fit,
                "authority_effect": "none",
            }
        )

    scored.sort(key=lambda item: (-item["score"], -item["task_fit"], item["name"]))

    if depth <= 3:
        rotating_slots = 0
    elif depth <= 7:
        rotating_slots = 1
    else:
        rotating_slots = min(7, max(3, len(scored)))

    selected = scored[:rotating_slots]
    challenger = None
    if challenger_slot and depth >= 7 and len(scored) > rotating_slots:
        # Deliberately pick the strongest unselected candidate below the main cut.
        challenger = scored[rotating_slots]
        if challenger["name"] not in {item["name"] for item in selected}:
            selected = [*selected, {**challenger, "slot": "challenger"}]

    return {
        "stable_core": STABLE_REVIEW_CORE,
        "depth": depth,
        "task_domains": tuple(sorted(domain_set)),
        "selected": tuple(selected),
        "ranked_candidates": tuple(scored),
        "challenger_slot": challenger,
        "decision_authority": False,
        "human_authority_final": True,
        "selection_rule": (
            "Stable core remains fixed; registered specialists rotate by task fit "
            "and evidence-backed performance."
        ),
    }


def status() -> dict[str, Any]:
    return {
        "component": "War Room Agent Ranking",
        "ready": True,
        "mode": "advisory_selection",
        "stable_core": STABLE_REVIEW_CORE,
        "rotating_pool": ROTATING_JUDGE_NAMES,
        "weights": SCORE_WEIGHTS,
        "challenger_slot": True,
        "rank_is_domain_specific": True,
        "decision_authority": False,
        "human_authority_final": True,
        "upgrade_only": True,
    }
