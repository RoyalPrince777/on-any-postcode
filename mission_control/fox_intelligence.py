"""Fox V2: bounded, advisory-only evidence and alternative assessment.

No network, mutation, autonomous execution, approvals or duplicate agent registry.
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

REQUIRED_PROOF = ("source", "reference", "observation")
PRODUCTION_PROOF = ("test_passed", "runtime_observed", "human_approved")


def evidence_valid(evidence: Mapping[str, Any]) -> bool:
    """Require a traceable source, reference and actual observation."""
    return all(isinstance(evidence.get(k), str) and bool(evidence[k].strip()) for k in REQUIRED_PROOF)


def rank_alternatives(options: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Deterministic advisory ranking; lower cost/risk/dependencies wins.

    Scores must be integers from 0 to 5; reversible is an explicit boolean.
    Invalid input fails closed instead of silently influencing ranking.
    """
    ranked = []
    for option in options:
        if not isinstance(option.get("name"), str) or not option["name"].strip():
            raise ValueError("named alternative required")
        scores = [option.get(k) for k in ("cost", "risk", "dependencies")]
        if any(type(v) is not int or not 0 <= v <= 5 for v in scores):
            raise ValueError("cost, risk, dependencies must be integers 0..5")
        if type(option.get("reversible")) is not bool:
            raise ValueError("reversible must be boolean")
        ranked.append(dict(option))
    return sorted(ranked, key=lambda o: (o["risk"], not o["reversible"], o["dependencies"], o["cost"], o["name"]))


def assess_mission(*, evidence: Mapping[str, Any], alternatives: list[Mapping[str, Any]],
                   dissent: list[Mapping[str, str]], recovery: Mapping[str, Any],
                   test_passed: bool = False, runtime_observed: bool = False,
                   human_approved: bool = False) -> dict[str, Any]:
    """Produce a read-only War Room-compatible advisory record, never a green gate."""
    valid = evidence_valid(evidence)
    recovery_ready = all(isinstance(recovery.get(k), str) and recovery[k].strip()
                         for k in ("backup_reference", "rollback_procedure"))
    recorded_dissent = []
    for item in dissent:
        if not all(isinstance(item.get(k), str) and item[k].strip()
                   for k in ("agent", "reason", "evidence_reference")):
            raise ValueError("dissent requires agent, reason and evidence reference")
        recorded_dissent.append(dict(item))
    ordered = rank_alternatives(alternatives)
    proof = valid and recovery_ready and test_passed is True and runtime_observed is True and human_approved is True
    return {
        "agent": "Fox", "mode": "advisory", "founder_final": True,
        "evidence_verified": valid, "recovery_ready": bool(recovery_ready),
        "alternatives": ordered, "recommended": ordered[0]["name"] if ordered else None,
        "dissent": recorded_dissent, "production_gate": "eligible_for_human_review" if proof else "blocked",
        "missing": [name for name, passed in (
            ("traceable_evidence", valid), ("recovery", recovery_ready),
            ("tests", test_passed is True), ("runtime", runtime_observed is True),
            ("founder_approval", human_approved is True)) if not passed],
    }
