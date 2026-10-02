"""OAP World Company Intelligence and commercial pressure-test protocol.

This is a first-party governance/planning layer. It does not impersonate independent
agents, grant legal authority, move money, file statutory documents, approve regulated
activity, or turn review votes into execution authority.

The Founder requested "700 stages". Canonically this is implemented as 700 review
checks inside one bounded mission, not 700 stop/start workflow stages:
7 review areas x 10 intelligence lenses x 10 evidence tests = 700 checks.
"""
from __future__ import annotations

from typing import Any, Iterable

from . import matrix_simulation, smi_judge_rotation

NAME = "OAP Company Intelligence"
SCOPE = "whole_oap_world"

REVIEW_AREAS: tuple[str, ...] = (
    "company",
    "music",
    "clothing",
    "print_on_demand",
    "rights_and_compliance",
    "commercial_finance",
    "platform_operations",
)

INTELLIGENCE_LENSES: tuple[str, ...] = (
    "truth",
    "evidence",
    "gap",
    "risk",
    "dependency",
    "architecture",
    "security",
    "compliance",
    "commercial_value",
    "recovery",
)

EVIDENCE_TESTS: tuple[str, ...] = (
    "current_source",
    "owner_or_authority",
    "timestamp_or_version",
    "functional_test",
    "integration_test",
    "permission_boundary",
    "financial_boundary",
    "legal_boundary",
    "rollback_or_recovery",
    "human_authority",
)

TOTAL_PROTOCOL_CHECKS = (
    len(REVIEW_AREAS) * len(INTELLIGENCE_LENSES) * len(EVIDENCE_TESTS)
)

HORMOZI_INTELLIGENCE: tuple[dict[str, str], ...] = (
    {"id": "dream_outcome", "question": "What result does the customer actually want?"},
    {"id": "perceived_likelihood", "question": "What evidence makes delivery believable?"},
    {"id": "time_delay", "question": "How quickly is useful value delivered?"},
    {"id": "effort_sacrifice", "question": "How much friction or sacrifice is required?"},
    {"id": "offer_stack", "question": "What exactly is included in the offer?"},
    {"id": "price_value_gap", "question": "Is value clear relative to the price?"},
    {"id": "unit_economics", "question": "Do revenue, costs and margin remain sustainable?"},
)

MUSIC_POLICY: dict[str, Any] = {
    "distribution_scope": "OAP-only",
    "external_platform_distribution": False,
    "external_distribution_future_assumption": False,
    "direct_purchase_primary": True,
    "streaming_royalty_dependency": False,
    "minimum_track_price_gbp": 1,
    "optional_pay_more": True,
    "rights_evidence_required": True,
    "artist_split_evidence_required": True,
}

CLOTHING_POLICY: dict[str, Any] = {
    "oap_brand_front_door": True,
    "pricing_evidence_required": True,
    "margin_evidence_required": True,
    "returns_and_sizing_evidence_required": True,
    "supplier_or_production_evidence_required": True,
}

PRINT_ON_DEMAND_POLICY: dict[str, Any] = {
    "is_production_method_not_separate_brand": True,
    "oap_market_front_door": True,
    "supplier_cost_evidence_required": True,
    "print_quality_evidence_required": True,
    "shipping_evidence_required": True,
    "returns_evidence_required": True,
    "margin_evidence_required": True,
}

COMMERCIAL_LANES: dict[str, dict[str, Any]] = {
    "music": MUSIC_POLICY,
    "clothing": CLOTHING_POLICY,
    "print_on_demand": PRINT_ON_DEMAND_POLICY,
}

REVIEW_AGENTS: tuple[str, ...] = matrix_simulation.TRAINING_PARTICIPANTS
CANONICAL_JUDGES: tuple[str, ...] = smi_judge_rotation.CANONICAL_JUDGE_NAMES
SEPARATE_GATES: tuple[str, ...] = smi_judge_rotation.SEPARATE_GATES

REQUIRED_REVIEW_NAMES: tuple[str, ...] = (
    "Bagheera",
    "Shere Khan",
    "Agent Smith",
    "Twinz",
    "Neo",
    "Morpheus",
    "Trinity",
    "Oracle",
    "Architect",
    "Keymaker",
    "Seraph",
)

VALID_VOTES = {"PASS", "FAIL", "ABSTAIN", "CONDITIONAL"}


def protocol_cells() -> tuple[tuple[str, str, str], ...]:
    """Return the deterministic 700-check review matrix."""

    return tuple(
        (area, lens, evidence_test)
        for area in REVIEW_AREAS
        for lens in INTELLIGENCE_LENSES
        for evidence_test in EVIDENCE_TESTS
    )


def review_plan(lane: str) -> dict[str, Any]:
    """Build a bounded review plan for one current commercial lane."""

    safe_lane = (lane or "").strip().lower()
    if safe_lane not in COMMERCIAL_LANES:
        raise ValueError(f"Unsupported commercial lane: {lane}")
    return {
        "name": NAME,
        "scope": SCOPE,
        "lane": safe_lane,
        "policy": dict(COMMERCIAL_LANES[safe_lane]),
        "hormozi_intelligence": HORMOZI_INTELLIGENCE,
        "protocol_check_count": TOTAL_PROTOCOL_CHECKS,
        "review_agents": REVIEW_AGENTS,
        "canonical_judges": CANONICAL_JUDGES,
        "separate_gates": SEPARATE_GATES,
        "review_mode": "registered-agent roles plus inspectable rule/evidence lenses",
        "simulated_independent_agent_claim": False,
        "votes_grant_execution": False,
        "guardian_required": True,
        "green_gate_required": True,
        "founder_final_required": True,
        "external_action_taken": False,
        "full_green": False,
    }


def tally_attributable_votes(votes: Iterable[dict[str, str]]) -> dict[str, Any]:
    """Tally only attributable reviewer votes carrying an evidence reference.

    A vote informs judgement only. It never grants execution, legal permission,
    regulatory approval, deployment or Founder Final.
    """

    allowed_reviewers = set(REVIEW_AGENTS) | set(CANONICAL_JUDGES)
    accepted: list[dict[str, str]] = []
    rejected: list[dict[str, str]] = []
    counts = {decision: 0 for decision in sorted(VALID_VOTES)}

    for raw_vote in votes:
        reviewer = str(raw_vote.get("reviewer", "")).strip()
        decision = str(raw_vote.get("decision", "")).strip().upper()
        evidence = str(raw_vote.get("evidence", "")).strip()
        normalized = {
            "reviewer": reviewer,
            "decision": decision,
            "evidence": evidence,
        }
        if reviewer not in allowed_reviewers or decision not in VALID_VOTES or not evidence:
            rejected.append(normalized)
            continue
        accepted.append(normalized)
        counts[decision] += 1

    return {
        "accepted": tuple(accepted),
        "rejected": tuple(rejected),
        "counts": counts,
        "attributable_vote_count": len(accepted),
        "votes_grant_execution": False,
        "founder_final_required": True,
    }


def status() -> dict[str, Any]:
    cells = protocol_cells()
    participant_names = set(REVIEW_AGENTS) | set(CANONICAL_JUDGES)
    return {
        "name": NAME,
        "scope": SCOPE,
        "commercial_lanes": tuple(COMMERCIAL_LANES),
        "hormozi_lens_count": len(HORMOZI_INTELLIGENCE),
        "review_area_count": len(REVIEW_AREAS),
        "intelligence_lens_count": len(INTELLIGENCE_LENSES),
        "evidence_test_count": len(EVIDENCE_TESTS),
        "protocol_check_count": len(cells),
        "protocol_is_checks_not_stages": True,
        "required_review_names_present": all(
            name in participant_names for name in REQUIRED_REVIEW_NAMES
        ),
        "matrix_participants_reused": True,
        "canonical_judges_reused": True,
        "guardian_and_green_gate_separate": SEPARATE_GATES
        == ("Guardian", "Green Gate"),
        "music_policy": dict(MUSIC_POLICY),
        "clothing_policy": dict(CLOTHING_POLICY),
        "print_on_demand_policy": dict(PRINT_ON_DEMAND_POLICY),
        "legal_authority_claimed": False,
        "regulatory_permission_claimed": False,
        "production_execution_granted": False,
        "human_authority_final": True,
        "full_green": False,
    }
