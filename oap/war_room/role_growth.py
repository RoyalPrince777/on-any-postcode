"""Evidence-first Role Growth War Room simulation for EARTH IS OUR TURF.

This module is advisory only. It never grants titles, SIKA, permissions, money,
or geographic authority. It turns explicit evidence flags into transparent
signals, percentages and a seven-star gate for Human Authority review.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

COUNCIL = (
    {
        "id": "shere_khan",
        "name": "Shere Khan",
        "lens": "Adversarial challenge",
        "focus": "Gaming, collusion, self-approval, duplicate proof and authority capture.",
    },
    {
        "id": "adam_smith",
        "name": "Adam Smith",
        "lens": "Economy and incentives",
        "focus": "SIKA, Created Value, monetisation and incentive friction.",
    },
    {
        "id": "bagheera",
        "name": "Bagheera",
        "lens": "Protection",
        "focus": "Privacy, safeguarding, permissions and minimum disclosure.",
    },
    {
        "id": "akela",
        "name": "Akela",
        "lens": "Governance",
        "focus": "Role scope, separation of duties, progression and appeals.",
    },
    {
        "id": "gyata",
        "name": "Gyata / Lion",
        "lens": "Authority and resilience",
        "focus": "Role lifecycle, inactivity, corruption resistance and recovery.",
    },
    {
        "id": "smi",
        "name": "SMI",
        "lens": "Whole-system synthesis",
        "focus": "Coherence across Matrix, Family Tree, Civic, OAP World and Chronicle.",
    },
)

PROTOCOL_21 = (
    ("clear_purpose", "Clear purpose", "smi"),
    ("born_local_global", "Born-local to global logic", "akela"),
    ("postcode_start", "Postcode starting point", "gyata"),
    ("choice_of_lane", "Choice of growth lane", "smi"),
    ("president_vp", "President / Vice President progression", "akela"),
    ("ceo_business", "CEO / business progression", "adam_smith"),
    ("matrix", "Matrix progression", "smi"),
    ("family_tree", "Family Tree progression", "bagheera"),
    ("royal_integrity", "Royal / traditional-title integrity", "akela"),
    ("intelligence", "Intelligence progression", "smi"),
    ("sika", "SIKA incentives", "adam_smith"),
    ("anti_gaming", "Anti-gaming controls", "shere_khan"),
    ("created_value", "Created Value proof", "adam_smith"),
    ("privacy", "Privacy choice", "bagheera"),
    ("youth", "Youth safeguards", "bagheera"),
    ("role_permissions", "Role permissions", "akela"),
    ("promotion_demotion", "Promotion / demotion", "shere_khan"),
    ("appeals", "Appeals / disputes", "akela"),
    ("monetisation", "Monetisation", "adam_smith"),
    ("cross_oap", "Cross-OAP integration", "smi"),
    ("scalability", "Long-term scalability", "gyata"),
)

SEVEN_STAR_GATE = (
    ("identity", "Identity"),
    ("proof", "Proof"),
    ("created_value", "Created Value"),
    ("responsibility", "Responsibility"),
    ("trust", "Trust / integrity"),
    ("scope_readiness", "Scope readiness"),
    ("human_gate", "Human approval where required"),
)

ROLE_LIFECYCLE = (
    "candidate",
    "active",
    "review",
    "renewed",
    "completed",
    "paused",
    "suspended",
    "retired",
    "legacy",
)

SENSITIVE_LANES = frozenset(
    {
        "president",
        "vice_president",
        "treasury",
        "youth_safeguarding",
        "high_level_civic",
        "sensitive_family_tree",
        "high_level_matrix",
        "traditional_title",
    }
)


def _signal(percent: int) -> str:
    if percent >= 94:
        return "green"
    if percent >= 85:
        return "purple"
    if percent >= 70:
        return "amber"
    return "red"


def _truth(value: object) -> bool:
    return value is True


def review_role_growth(
    evidence: Mapping[str, object],
    *,
    lane: str = "general",
    human_approval_required: bool | None = None,
) -> dict[str, Any]:
    """Return a bounded evidence score; missing evidence always fails closed."""

    checks = []
    for check_id, name, challenger in PROTOCOL_21:
        passed = _truth(evidence.get(check_id))
        checks.append(
            {
                "id": check_id,
                "name": name,
                "challenger": challenger,
                "passed": passed,
                "signal": "green" if passed else "amber",
            }
        )

    passed_count = sum(item["passed"] for item in checks)
    percent = round((passed_count / len(checks)) * 100)

    required_human = (
        lane in SENSITIVE_LANES
        if human_approval_required is None
        else bool(human_approval_required)
    )
    stars = []
    for gate_id, name in SEVEN_STAR_GATE:
        if gate_id == "human_gate" and not required_human:
            passed = True
            evidence_state = "not_required"
        else:
            passed = _truth(evidence.get(f"gate_{gate_id}"))
            evidence_state = "proven" if passed else "missing"
        stars.append(
            {
                "id": gate_id,
                "name": name,
                "passed": passed,
                "evidence_state": evidence_state,
            }
        )

    star_count = sum(item["passed"] for item in stars)
    blockers = [
        item["name"] for item in checks if not item["passed"]
    ]
    gate_blockers = [
        item["name"] for item in stars if not item["passed"]
    ]

    anti_gaming_controls = {
        "no_self_certification": _truth(evidence.get("no_self_certification")),
        "duplicate_proof_detection": _truth(evidence.get("duplicate_proof_detection")),
        "independent_confirmation": _truth(evidence.get("independent_confirmation")),
        "anti_collusion": _truth(evidence.get("anti_collusion")),
        "no_sika_only_promotion": _truth(evidence.get("no_sika_only_promotion")),
        "separation_of_duties": _truth(evidence.get("separation_of_duties")),
    }
    anti_gaming_ready = all(anti_gaming_controls.values())

    traditional_title_authenticated = (
        _truth(evidence.get("traditional_title_authenticated"))
        if lane == "traditional_title"
        else None
    )

    can_recommend_promotion = (
        percent >= 94
        and star_count == len(SEVEN_STAR_GATE)
        and anti_gaming_ready
        and (traditional_title_authenticated is not False)
    )

    return {
        "system": "EARTH IS OUR TURF Role Growth Engine",
        "mode": "simulation_only",
        "decision_authority": False,
        "human_authority_final": True,
        "lane": lane,
        "signal": _signal(percent),
        "percent": percent,
        "protocol_passed": passed_count,
        "protocol_total": len(checks),
        "stars": star_count,
        "stars_total": len(stars),
        "stars_display": "★" * star_count + "☆" * (len(stars) - star_count),
        "checks": checks,
        "seven_star_gate": stars,
        "anti_gaming": {
            "ready": anti_gaming_ready,
            "controls": anti_gaming_controls,
        },
        "traditional_title_authenticated": traditional_title_authenticated,
        "role_lifecycle": ROLE_LIFECYCLE,
        "blockers": tuple(blockers),
        "gate_blockers": tuple(gate_blockers),
        "can_recommend_promotion": can_recommend_promotion,
        "recommendation": (
            "Evidence supports referral to Human Authority."
            if can_recommend_promotion
            else "Remain in review; unresolved evidence or governance gates remain."
        ),
    }


def status() -> dict[str, Any]:
    return {
        "component": "Role Growth War Room",
        "ready": True,
        "mode": "simulation_only",
        "decision_authority": False,
        "human_authority_final": True,
        "protocol_checks": len(PROTOCOL_21),
        "gate_stars": len(SEVEN_STAR_GATE),
        "council": COUNCIL,
        "anti_gaming_fail_closed": True,
        "traditional_title_boundary": (
            "OAP cultural progression never authenticates a real-world traditional title."
        ),
        "privacy_boundary": "Proof and publicity are separate.",
        "sika_boundary": "SIKA can support progression but cannot buy authority.",
    }
