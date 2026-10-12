"""Evidence gates for mission-adaptive Alliance Intelligence.

An advisory read-only layer over existing War Room scoring; never grants authority.
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from oap.war_room.agent_selection import SCORE_WEIGHTS, score_agent

REQUIRED_EVIDENCE_FIELDS = frozenset(SCORE_WEIGHTS)


def evaluate_pac_evidence(
    metrics: Mapping[str, object] | None,
    evidence: Mapping[str, str] | None,
    *,
    is_registered: bool,
    independent_review: bool,
) -> dict[str, Any]:
    """Do not turn missing evidence, zero defaults, or self-review into a rating."""
    missing = sorted(
        key for key in REQUIRED_EVIDENCE_FIELDS
        if not metrics or key not in metrics
        or not evidence or not str(evidence.get(key, "")).strip()
    )
    if not is_registered:
        return {"status": "INELIGIBLE", "score": None, "reason": "unregistered",
                "missing_evidence": missing, "authority_effect": "none"}
    if not independent_review:
        return {"status": "REVIEW_REQUIRED", "score": None,
                "reason": "independent review missing",
                "missing_evidence": missing, "authority_effect": "none"}
    if missing:
        return {"status": "NOT_RATED", "score": None,
                "reason": "missing metric or provenance",
                "missing_evidence": missing, "authority_effect": "none"}
    if any(isinstance(metrics[k], bool) or not isinstance(metrics[k], (int, float))
           or not 0 <= metrics[k] <= 100 for k in REQUIRED_EVIDENCE_FIELDS):
        return {"status": "INVALID", "score": None,
                "reason": "metric outside 0-100 numeric range",
                "missing_evidence": [], "authority_effect": "none"}
    result = score_agent(metrics)
    return {"status": "EVIDENCE_SUBMITTED", "score": result["score"],
            "tier": result["tier"], "authority_effect": "none",
            "verification_note": "Provenance supplied; source authenticity requires external verification"}
