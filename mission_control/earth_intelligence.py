"""Runtime projection for the approved OAP Earth Intelligence world.

Earth Intelligence powers the EARTH OUR TURF place experience.  It remains one
of the seven governed Intelligence worlds, not another OAP brain or agent
family.  Weather is the first live environmental input; wider Earth domains
remain fail-closed until real sources exist.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

COMPONENTS = (
    "weather_climate",
    "atmosphere",
    "land",
    "water",
    "ecosystems",
    "agriculture",
    "resources",
    "disaster_awareness",
    "sustainability",
    "planetary_wellbeing",
)

# Local is an umbrella, not a single administrative type. Borough/District is
# deliberately kept inside the Local family while every country can map its
# real administrative names onto these OAP concepts.
LOCAL_DETAIL_LEVELS: tuple[str, ...] = (
    "spot",
    "street_block",
    "estate_village_neighbourhood",
    "ward_local_area",
    "postcode_or_equivalent",
    "borough_district_or_equivalent",
)
EARTH_OUR_TURF_LEVELS: tuple[str, ...] = (
    "local",
    "region_county_or_equivalent",
    "country",
    "continent",
    "global",
)

EARTH_OUR_TURF_COMPOSITION: tuple[dict[str, str], ...] = (
    {"source": "Earth Intelligence", "role": "place, land, climate, nature and environmental context"},
    {"source": "Civic Intelligence", "role": "community and public-service context"},
    {"source": "Civilisation Intelligence", "role": "history, culture and institutions"},
    {"source": "Language Intelligence", "role": "languages, variants and communication context"},
    {"source": "Life Intelligence", "role": "practical education, skills and real-life context"},
    {"source": "Movement Intelligence", "role": "routes, transport and movement between places"},
    {"source": "Signal", "role": "current trusted updates"},
    {"source": "Chronicle", "role": "place memory and stories"},
    {"source": "Community Power", "role": "participation, leadership, education and Nature growth"},
)

NATURE_GROWTH_MODEL: tuple[dict[str, str], ...] = (
    {"id": "seed", "emoji": "🌱", "meaning": "How an OAP story or connection begins."},
    {"id": "branches", "emoji": "🌿", "meaning": "How connections spread."},
    {"id": "leaves", "emoji": "🍃", "meaning": "Active people, creators, businesses, communities and opportunities."},
    {"id": "bloom", "emoji": "🌺", "meaning": "Something new launches or comes alive."},
    {"id": "harvest", "emoji": "🥭", "meaning": "Real outcomes or value are created."},
    {"id": "journey", "emoji": "🕰️", "meaning": "How the growth develops over time."},
    {"id": "canopy", "emoji": "🌳", "meaning": "Overall Local-to-Global reach."},
)


def _text(value: object) -> str:
    return str(value or "").strip()


def _place_model() -> dict[str, Any]:
    return {
        "experience": "EARTH OUR TURF",
        "tagline": "Born Local. Built Global. Earth Is Our Turf.",
        "canonical_spatial_binding": "EARTH_OUR_TURF_LOCAL_TO_GLOBAL",
        "local_detail_levels": LOCAL_DETAIL_LEVELS,
        "earth_levels": EARTH_OUR_TURF_LEVELS,
        "borough_is_local": True,
        "country_specific_admin_mapping_required": True,
        "composition": EARTH_OUR_TURF_COMPOSITION,
        "community_power": {
            "owns_leadership_and_education": True,
            "owns_nature_growth_model": True,
            "nature_growth_model": NATURE_GROWTH_MODEL,
            "hybrid_governance": HYBRID_COMMUNITY_GOVERNANCE,
            "progression_levels": COMMUNITY_GOVERNANCE_LEVELS,
            "progression_checks": COMMUNITY_PROGRESS_CHECKS,
            "leadership_roles": COMMUNITY_HYBRID_ROLES,
        },
        "world_rooms_role": "community_interaction_feature_inside_places",
    }


def from_weather(weather: Mapping[str, Any]) -> dict[str, Any]:
    """Project verified Weather Intelligence into bounded Earth context."""

    weather_signal = weather.get("intelligence")
    weather_ready = (
        isinstance(weather_signal, Mapping)
        and bool(_text(weather_signal.get("observation_time")))
        and _text(weather_signal.get("advisory_level")) != "unavailable"
    )
    return {
        "name": "Earth Intelligence",
        "world_id": "earth",
        "architecture_passed": True,
        "component_count": len(COMPONENTS),
        "components": COMPONENTS,
        "nature_organ": "OAP Nature",
        "weather_intelligence_connected": weather_ready,
        # Compatibility field retained for existing clients; canonical binding is
        # exposed separately and new code must use the Local-to-Global model.
        "spatial_binding": "THE_SPOT_POSTCODE_TO_UNIVERSE",
        "canonical_spatial_binding": "EARTH_OUR_TURF_LOCAL_TO_GLOBAL",
        "place_model": _place_model(),
        "current_environment": {
            "condition": _text(weather_signal.get("condition")) if weather_ready else "",
            "advisory_level": _text(weather_signal.get("advisory_level")) if weather_ready else "unavailable",
            "rain_signal": _text(weather_signal.get("rain_signal")) if weather_ready else "unavailable",
            "wind_signal": _text(weather_signal.get("wind_signal")) if weather_ready else "unavailable",
            "thermal_signal": _text(weather_signal.get("thermal_signal")) if weather_ready else "unavailable",
            "observation_time": _text(weather_signal.get("observation_time")) if weather_ready else "",
        },
        "coverage": {
            "weather": "live_bootstrap" if weather_ready else "unavailable",
            "atmosphere": "weather_signals_only" if weather_ready else "unavailable",
            "land": "spatial_context_only",
            "water": "not_connected",
            "ecosystems": "not_connected",
            "agriculture": "not_connected",
            "resources": "not_connected",
            "disaster_awareness": "weather_advisory_only" if weather_ready else "not_connected",
            "sustainability": "architecture_only",
            "planetary_wellbeing": "architecture_only",
        },
        "live_environment_ready": weather_ready,
        "full_earth_runtime_ready": False,
        "human_authority_final": True,
        "can_execute": False,
        "truth_boundary": (
            "Earth Intelligence currently uses verified place context and Weather Intelligence only. "
            "EARTH OUR TURF composition is defined, but water, ecosystem, agriculture, resource, "
            "wider disaster and broader place-knowledge feeds remain unconnected and are never inferred."
        ),
    }


def status(*, weather_ready: bool) -> dict[str, Any]:
    """Return architecture/readiness without making network calls."""

    return {
        "name": "Earth Intelligence",
        "world_id": "earth",
        "architecture_passed": True,
        "component_count": len(COMPONENTS),
        "components": COMPONENTS,
        "nature_organ_connected": True,
        "weather_intelligence_connected": bool(weather_ready),
        "the_spot_connected": True,
        "spatial_binding": "POSTCODE_TO_UNIVERSE",
        "canonical_spatial_binding": "EARTH_OUR_TURF_LOCAL_TO_GLOBAL",
        "place_model": _place_model(),
        "full_earth_runtime_ready": False,
        "human_authority_final": True,
        "can_execute": False,
        "truth_boundary": (
            "The Earth Intelligence world, EARTH OUR TURF place model and OAP Nature organ are present. "
            "Weather is the first live sensing connection; broader Earth and place observations remain gated."
        ),
    }


# Community Power uses the existing Earth locality hierarchy; it is not an
# elected government, a second identity service or an autonomous SMI authority.
COMMUNITY_GOVERNANCE_LEVELS = (
    "postcode", "borough_district_or_equivalent",
    "region_county_or_equivalent", "country", "continent", "global",
)
HYBRID_COMMUNITY_GOVERNANCE = {
    "model": "hybrid",
    "community_owner": "Community Power",
    "executive_role": "CEO / authorised operational lead",
    "community_role": "Elected or legitimately appointed community council",
    "executive_scope": "Approved operations only; no control of community votes",
    "council_scope": "Community proposals, oversight and member representation",
    "one_my_card": True,
    "public_browsing_requires_id": False,
    "government_id_mandatory_for_public_browsing": False,
    "youth_safeguarding_required": True,
    "forced_membership": False,
    "biometric_eligibility_requirement": False,
    "automated_elections": False,
    "automatic_promotion": False,
    "agent_authority": False,
    "guardian_hrm_required": True,
    "human_authority_final": True,
}
# One evidenced milestone for each 3-check segment, not 21 invented stages.
COMMUNITY_PROGRESS_CHECKS = (
    ("formation", ("participation", "member_consent", "community_scope")),
    ("learning", ("learning_access", "skill_evidence", "youth_separation")),
    ("projects", ("project_proposals", "team_permissions", "outcome_evidence")),
    ("support", ("needs_review", "voluntary_assistance", "privacy_review")),
    ("culture", ("community_activities", "fair_participation", "safety_review")),
    ("leadership", ("nomination_rules", "oversight_rules", "appeal_process")),
    ("verification", ("evidence_integrity", "independent_review", "founder_release_gate")),
)


def review_community_hybrid_progress(
    level: object, evidence: object
) -> dict[str, Any]:
    """Read-only, fail-closed 7x3 evidence review; never promotes or appoints.

    Evidence must be externally verified before it is supplied. This pure
    function cannot attest the authenticity of receipts or hold an election.
    """
    result: dict[str, Any] = {
        "model": "hybrid",
        "level": str(level or ""),
        "verified_checks": 0,
        "total_checks": 21,
        "review_eligible": False,
        "promoted": False,
        "leader_appointed": False,
        "votes_cast": 0,
        "can_execute": False,
        "human_authority_final": True,
        "reason": "evidence_unverified",
    }
    if level not in COMMUNITY_GOVERNANCE_LEVELS:
        return {**result, "reason": "invalid_geography"}
    if not isinstance(evidence, Mapping):
        return result
    required = tuple(check for _, checks in COMMUNITY_PROGRESS_CHECKS for check in checks)
    # Fail closed if any check is missing or not an explicit verified receipt.
    passed = tuple(
        check for check in required
        if isinstance(evidence.get(check), Mapping)
        and evidence[check].get("verified") is True
        and isinstance(evidence[check].get("receipt_id"), str)
        and bool(evidence[check]["receipt_id"].strip())
    )
    receipt_ids = tuple(evidence[c]["receipt_id"].strip() for c in passed)
    if len(set(receipt_ids)) != len(receipt_ids):
        return {**result, "reason": "duplicate_evidence"}
    complete = len(passed) == len(required)
    return {
        **result,
        "verified_checks": len(passed),
        "review_eligible": complete and level != "global",
        "reason": "requires_independent_approval" if complete else "checks_incomplete",
    }


# Optional positions under existing Hybrid Community Power, not automatic offices.
# Small communities may leave positions vacant or combine compatible duties.
# Independent assurance lanes must not report through the role they review.
COMMUNITY_HYBRID_ROLES: tuple[dict[str, str], ...] = (
    {"id": "president", "title": "President", "lane": "community", "purpose": "Representation and community voice"},
    {"id": "vice_president", "title": "Vice President", "lane": "community", "purpose": "Deputy community representation"},
    {"id": "council_chair", "title": "Council Chair", "lane": "community", "purpose": "Chair community meetings and procedures"},
    {"id": "council_secretary", "title": "Council Secretary", "lane": "community", "purpose": "Minutes, records and agendas"},
    {"id": "community_treasurer", "title": "Community Treasurer", "lane": "community", "purpose": "Independent community fund oversight"},
    {"id": "ceo", "title": "CEO", "lane": "operations", "purpose": "Authorised operational delivery"},
    {"id": "deputy_ceo", "title": "Deputy CEO", "lane": "operations", "purpose": "Operational continuity"},
    {"id": "operations_director", "title": "Operations Director", "lane": "operations", "purpose": "Project delivery and logistics"},
    {"id": "finance_director", "title": "Finance Director", "lane": "operations", "purpose": "Budgeting subject to approved controls"},
    {"id": "technology_director", "title": "Technology Director", "lane": "operations", "purpose": "Technology and system operations"},
    {"id": "education_director", "title": "Education Director", "lane": "operations", "purpose": "Learning and skills coordination"},
    {"id": "youth_director", "title": "Youth Director", "lane": "operations", "purpose": "Safeguarded youth programme coordination"},
    {"id": "community_support_lead", "title": "Community Support Lead", "lane": "operations", "purpose": "Voluntary aid and support coordination"},
    {"id": "projects_director", "title": "Projects Director", "lane": "operations", "purpose": "Project planning and coordination"},
    {"id": "culture_sports_director", "title": "Culture & Sports Director", "lane": "operations", "purpose": "Community activities and Arena coordination"},
    {"id": "environment_director", "title": "Environment Director", "lane": "operations", "purpose": "Nature and sustainability"},
    {"id": "business_enterprise_lead", "title": "Business & Enterprise Lead", "lane": "operations", "purpose": "Business opportunity support"},
    {"id": "communications_director", "title": "Communications Director", "lane": "operations", "purpose": "Signal and community communications"},
    {"id": "partnerships_director", "title": "Partnerships Director", "lane": "operations", "purpose": "External and internal partnerships"},
    {"id": "safeguarding_lead", "title": "Independent Safeguarding Lead", "lane": "independent", "purpose": "Independent safeguarding escalation and review"},
    {"id": "audit_lead", "title": "Independent Audit Lead", "lane": "independent", "purpose": "Independent evidence and integrity review"},
)


def review_community_role_assignment(
    role_id: object, member: object, *, governance_level: object
) -> dict[str, object]:
    """Read-only gate for a proposed role, never an appointment or election.

    Caller-supplied evidence is not independently authenticated here.
    Actual appointment requires the existing My Card identity, independent
    safeguarding checks, authenticated governance records and human approval.
    """
    result: dict[str, object] = {
        "eligible_for_review": False,
        "assigned": False,
        "vote_cast": False,
        "authority_granted": False,
        "public_profile_created": False,
        "reason": "unverified",
        "founder_final": True,
    }
    roles = {row["id"]: row for row in COMMUNITY_HYBRID_ROLES}
    if role_id not in roles:
        return {**result, "reason": "role_unknown"}
    if governance_level not in COMMUNITY_GOVERNANCE_LEVELS:
        return {**result, "reason": "geography_unknown"}
    if not isinstance(member, Mapping):
        return result
    if member.get("my_card_verified") is not True or member.get("membership_verified") is not True:
        return {**result, "reason": "membership_unverified"}
    if member.get("role_opt_in") is not True:
        return {**result, "reason": "consent_missing"}
    if member.get("age_band") != "adult":
        return {**result, "reason": "adult_eligibility_unverified"}
    if member.get("safeguarding_clear") is not True:
        return {**result, "reason": "safeguarding_unverified"}
    if member.get("conflict_review_clear") is not True:
        return {**result, "reason": "conflicts_unverified"}
    if roles[role_id]["lane"] == "independent" and member.get("independent_review_clear") is not True:
        return {**result, "reason": "independence_unverified"}
    return {**result, "eligible_for_review": True, "reason": "human_appointment_required"}
