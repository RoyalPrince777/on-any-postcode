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


def compare_fox_assessments(*, fox: Mapping[str, Any], foxy: Mapping[str, Any]) -> dict[str, Any]:
    """Compare two independent advisory assessments without inventing learning or rank."""
    assessments = {}
    for name, item in (("Fox", fox), ("Foxy", foxy)):
        if not isinstance(item, Mapping) or item.get("agent") != name or item.get("mode") != "advisory":
            raise ValueError(f"{name} must provide its own advisory assessment")
        if item.get("production_gate") not in ("blocked", "eligible_for_human_review"):
            raise ValueError("invalid production gate")
        if item.get("founder_final") is not True:
            raise ValueError("Founder Final must be preserved")
        recommendation = item.get("recommended")
        if recommendation is not None and (not isinstance(recommendation, str) or not recommendation.strip()):
            raise ValueError("recommendation must be non-empty text or None")
        assessments[name] = dict(item)
    recommendations = {name: item.get("recommended") for name, item in assessments.items()}
    agreement = recommendations["Fox"] is not None and recommendations["Fox"] == recommendations["Foxy"]
    return {
        "mode": "advisory", "founder_final": True,
        "agents": assessments, "recommendations": recommendations,
        "agreement": agreement, "needs_review": not agreement,
        "production_gate": "blocked",
        "learning_verified": False, "rank_change": None,
    }


def assess_foxy_mission(**kwargs: Any) -> dict[str, Any]:
    """Give FOXY an independent advisory record using the existing proof gates."""
    record = assess_mission(**kwargs)
    return {**record, "agent": "Foxy"}



def assess_fox_routes(*, routes: list[Mapping[str, Any]],
                      blocked_route_names: list[str] | None = None) -> dict[str, Any]:
    """FOX-only route discovery assessment over supplied candidate routes.

    This does not fetch map data, calculate road geometry, or dispatch travel.
    Unknown or blocked routes never become recommendations.
    """
    blocked = blocked_route_names if blocked_route_names is not None else []
    if any(not isinstance(name, str) or not name.strip() for name in blocked):
        raise ValueError("blocked route names must be non-empty strings")
    if len(set(blocked)) != len(blocked):
        raise ValueError("duplicate blocked route")
    if not isinstance(routes, list):
        raise TypeError("routes must be a list")
    names: set[str] = set()
    eligible = []
    for route in routes:
        if not isinstance(route, Mapping):
            raise TypeError("route must be a mapping")
        name = route.get("name")
        if not isinstance(name, str) or not name.strip() or name in names:
            raise ValueError("route names must be unique non-empty strings")
        names.add(name)
        if name in blocked:
            continue
        eligible.append(route)
    ranked = rank_alternatives(eligible)
    return {
        "agent": "Fox", "specialism": "route_reconnaissance",
        "mode": "advisory", "founder_final": True,
        "guardian_review_required": True, "production_gate": "blocked",
        "route_data_verified": False,
        "alternatives": ranked,
        "recommended": ranked[0]["name"] if ranked else None,
        "blocked_routes": sorted(set(blocked).intersection(names)),
        "missing": ["verified_route_source", "live_navigation_proof"],
    }


def assess_foxy_routes(*, routes: list[Mapping[str, Any]],
                       blocked_route_names: list[str] | None = None) -> dict[str, Any]:
    """FOXY-only alternative strategy: prefer reversibility before risk.

    Same validated candidates and exclusion rules as FOX; no live navigation.
    """
    fox_record = assess_fox_routes(routes=routes, blocked_route_names=blocked_route_names)
    ranked = sorted(
        fox_record["alternatives"],
        key=lambda o: (not o["reversible"], o["risk"], o["dependencies"], o["cost"], o["name"]),
    )
    return {
        **fox_record,
        "agent": "Foxy",
        "specialism": "route_contingency_strategy",
        "alternatives": ranked,
        "recommended": ranked[0]["name"] if ranked else None,
    }


def compare_route_strategies(*, routes: list[Mapping[str, Any]],
                             blocked_route_names: list[str] | None = None) -> dict[str, Any]:
    """Contrast FOX route risk with FOXY reversible contingency priorities."""
    fox = assess_fox_routes(routes=routes, blocked_route_names=blocked_route_names)
    foxy = assess_foxy_routes(routes=routes, blocked_route_names=blocked_route_names)
    return compare_fox_assessments(fox=fox, foxy=foxy)
