"""Humanitarian Legal Intelligence for International Humanitarian Intelligence.

This module identifies potentially relevant legal and protection frameworks for civilian
humanitarian work. It is a legal-routing and evidence-boundary capability, not a court,
law firm, sanctions authority, conflict-classification authority, or source of final legal
advice. Jurisdiction-specific conclusions require current primary sources and appropriate
qualified review. Human Authority remains final for OAP decisions.
"""

from __future__ import annotations

from typing import Any

HUMANITARIAN_LEGAL_REGIMES: tuple[dict[str, str], ...] = (
    {
        "id": "ihl",
        "name": "International Humanitarian Law",
        "purpose": "Armed-conflict rules including civilian protection, distinction, precautions, humane treatment, medical protection and relief.",
    },
    {
        "id": "human_rights",
        "name": "International Human Rights Law",
        "purpose": "Rights and dignity protections that may operate alongside other legal regimes, including during armed conflict.",
    },
    {
        "id": "refugee_displacement",
        "name": "Refugee, Asylum, Displacement & Statelessness Law",
        "purpose": "Protection context for refugees, asylum seekers, internally displaced people, stateless people and migrants.",
    },
    {
        "id": "international_criminal",
        "name": "International Criminal Law",
        "purpose": "Recognise possible serious-law concerns for escalation and evidence preservation without adjudication or guilt findings.",
    },
    {
        "id": "disaster_idrl",
        "name": "Disaster Law & International Disaster Response Law",
        "purpose": "Domestic disaster preparedness/response and legal facilitation of international relief, personnel, goods, equipment and services.",
    },
    {
        "id": "law_of_land",
        "name": "Law of the Land",
        "purpose": "Resolve the current domestic law actually applicable to the country, region and local authority concerned.",
    },
    {
        "id": "customary_international",
        "name": "Customary International Law",
        "purpose": "Identify relevant customary international rules separately from treaty and domestic law.",
    },
    {
        "id": "traditional_customary",
        "name": "Traditional & Customary Law",
        "purpose": "Record local, Indigenous or traditional legal context only where its status under the applicable domestic legal order is verified.",
    },
    {
        "id": "child_protection",
        "name": "Child Humanitarian Protection Law",
        "purpose": "High-protection safeguards for children, family tracing, exploitation risk, recruitment risk, healthcare and education continuity.",
    },
    {
        "id": "disability_rights",
        "name": "Accessibility & Disability Rights Law",
        "purpose": "Protection and inclusion for people with disabilities in emergencies, evacuation, communication, shelter, transport and aid access.",
    },
    {
        "id": "health_medical",
        "name": "Humanitarian Health Law & Medical Protection",
        "purpose": "Medical protection, confidentiality, consent, care navigation, professional rules and public-health legal context.",
    },
    {
        "id": "data_privacy",
        "name": "Humanitarian Data & Privacy Law",
        "purpose": "Data minimisation, lawful processing, security, retention, disclosure controls and protection-by-design for vulnerable people.",
    },
    {
        "id": "digital_cyber",
        "name": "Digital Humanitarian Protection Law",
        "purpose": "Protect civilian digital infrastructure, humanitarian databases, identity systems, communications and emergency information from harmful use.",
    },
    {
        "id": "cultural_property",
        "name": "Cultural Heritage Protection Law",
        "purpose": "Protect cultural property, archives, museums, sacred places and heritage in conflict and emergency contexts.",
    },
    {
        "id": "environment",
        "name": "Humanitarian Environmental Protection Law",
        "purpose": "Identify protections concerning water, agriculture, ecosystems, contamination, dangerous installations and civilian environmental harm.",
    },
    {
        "id": "sanctions_humanitarian",
        "name": "Sanctions, Counterterrorism & Humanitarian Exemptions",
        "purpose": "Flag sanctions/counterterrorism constraints and humanitarian exemptions without issuing transaction clearance.",
    },
    {
        "id": "humanitarian_principles",
        "name": "Humanitarian Principles",
        "purpose": "Apply humanity, neutrality, impartiality and independence as operational principles, while keeping them distinct from statutory law.",
    },
)

HUMANITARIAN_PRINCIPLES: tuple[str, ...] = (
    "humanity",
    "neutrality",
    "impartiality",
    "independence",
)

PROTECTED_PERSON_CONTEXTS: tuple[str, ...] = (
    "civilians",
    "wounded_and_sick",
    "medical_personnel",
    "humanitarian_personnel",
    "detainees_and_persons_hors_de_combat",
    "children",
    "people_with_disabilities",
    "older_people",
    "refugees_and_asylum_seekers",
    "internally_displaced_people",
    "stateless_people",
    "missing_people_and_families",
)

HUMANITARIAN_DATA_LEVELS: tuple[dict[str, Any], ...] = (
    {
        "level": 0,
        "name": "Public",
        "examples": ("verified_general_warning", "public_service_information"),
        "public_default": True,
    },
    {
        "level": 1,
        "name": "Operational",
        "examples": ("non_sensitive_logistics", "aggregate_service_status"),
        "public_default": False,
    },
    {
        "level": 2,
        "name": "Protected",
        "examples": ("contact_information", "household_information"),
        "public_default": False,
    },
    {
        "level": 3,
        "name": "Highly Sensitive",
        "examples": ("health", "disability", "child", "refugee_or_displacement_status"),
        "public_default": False,
    },
    {
        "level": 4,
        "name": "Life-Critical",
        "examples": (
            "precise_civilian_location",
            "safe_house",
            "survivor_or_witness_location",
            "family_reunification_location",
        ),
        "public_default": False,
    },
)

# OAP internal survival-and-protection ethic. This is deliberately NOT law.
OAP_LAW_OF_THE_JUNGLE: tuple[str, ...] = (
    "Protect the vulnerable.",
    "Survival never overrides humanity.",
    "Strength protects; it does not prey.",
    "The Pack does not abandon its own.",
    "Warn before danger where doing so is safe and lawful.",
    "Share scarce essentials by urgent civilian need.",
    "Protect children with the highest safeguarding priority.",
    "Protect the wounded and sick.",
    "Do not expose another civilian's precise location by default.",
    "No targeting of people.",
    "No exploitation during chaos.",
    "Knowledge carries responsibility.",
    "Respect applicable law and verified humanitarian protections.",
    "Human Authority remains final for OAP decisions.",
)

PRIMARY_SOURCE_FAMILIES: tuple[dict[str, str], ...] = (
    {
        "id": "icrc_ihl",
        "name": "ICRC / Geneva Conventions / IHL resources",
        "role": "IHL, customary IHL, domestic implementation, missing persons and humanitarian data protection context.",
    },
    {
        "id": "un_human_rights",
        "name": "United Nations human-rights treaty system",
        "role": "Human rights, child protection and disability-rights treaty context.",
    },
    {
        "id": "unhcr",
        "name": "UNHCR refugee-protection resources",
        "role": "Refugee, asylum, displacement, statelessness and protection context.",
    },
    {
        "id": "ifrc_disaster_law",
        "name": "IFRC Disaster Law / IDRL",
        "role": "Disaster law, international disaster assistance and domestic preparedness/response context.",
    },
    {
        "id": "un_security_council",
        "name": "UN Security Council sanctions resources",
        "role": "Sanctions regimes and humanitarian exemptions such as Resolution 2664 and successors.",
    },
    {
        "id": "unesco_cultural_property",
        "name": "UNESCO cultural-property treaty resources",
        "role": "1954 Hague Convention and related cultural-property protection instruments.",
    },
    {
        "id": "domestic_primary_law",
        "name": "Official domestic legislation, courts and regulators",
        "role": "Current law of the land for the actual jurisdiction; country-specific evidence is mandatory.",
    },
)


def classify_humanitarian_data(
    *,
    health: bool = False,
    disability: bool = False,
    child: bool = False,
    refugee_or_displacement_status: bool = False,
    contact_or_household: bool = False,
    precise_civilian_location: bool = False,
    safe_house_or_witness: bool = False,
) -> dict[str, Any]:
    """Return the highest required humanitarian data-protection level."""

    level = 0
    reasons: list[str] = []
    if contact_or_household:
        level = max(level, 2)
        reasons.append("contact_or_household")
    if health or disability or child or refugee_or_displacement_status:
        level = max(level, 3)
        if health:
            reasons.append("health")
        if disability:
            reasons.append("disability")
        if child:
            reasons.append("child")
        if refugee_or_displacement_status:
            reasons.append("refugee_or_displacement_status")
    if precise_civilian_location or safe_house_or_witness:
        level = 4
        if precise_civilian_location:
            reasons.append("precise_civilian_location")
        if safe_house_or_witness:
            reasons.append("safe_house_or_witness")
    definition = next(item for item in HUMANITARIAN_DATA_LEVELS if item["level"] == level)
    return {
        "level": level,
        "name": definition["name"],
        "reasons": tuple(reasons),
        "public_default": bool(definition["public_default"]),
        "data_minimisation_required": level >= 2,
        "encryption_required_target": level >= 2,
        "retention_limit_required": level >= 2,
        "precise_location_public": False if level == 4 else None,
        "human_review_required": level >= 3,
    }


def resolve_humanitarian_legal_envelope(
    *,
    country: str,
    situation_type: str,
    region: str | None = None,
    armed_conflict_status: str = "unknown",
    cross_border: bool = False,
    displacement: bool = False,
    involves_children: bool = False,
    involves_disability: bool = False,
    involves_health: bool = False,
    involves_personal_data: bool = False,
    involves_precise_location: bool = False,
    involves_cultural_property: bool = False,
    involves_environmental_harm: bool = False,
    involves_sanctions: bool = False,
    primary_sources_verified: bool = False,
) -> dict[str, Any]:
    """Identify legal frameworks to review without issuing a final legal conclusion."""

    clean_country = " ".join(str(country or "").split()).strip()
    clean_situation = " ".join(str(situation_type or "").split()).strip().casefold()
    if not clean_country:
        return {
            "accepted": False,
            "reason": "country_required_for_law_of_land",
            "legal_conclusion": False,
            "qualified_legal_review_required": True,
            "human_authority_final": True,
        }
    if not clean_situation:
        return {
            "accepted": False,
            "reason": "situation_type_required",
            "legal_conclusion": False,
            "qualified_legal_review_required": True,
            "human_authority_final": True,
        }

    regimes: list[str] = ["human_rights", "law_of_land", "humanitarian_principles"]
    conflict = armed_conflict_status.strip().casefold()
    armed_conflict_known = conflict in {
        "international",
        "non_international",
        "occupation",
        "armed_conflict",
    }
    if armed_conflict_known:
        regimes.extend(("ihl", "customary_international", "international_criminal"))
    disaster_terms = ("disaster", "earthquake", "flood", "storm", "fire", "pandemic", "emergency")
    if any(term in clean_situation for term in disaster_terms):
        regimes.append("disaster_idrl")
    if cross_border or displacement:
        regimes.append("refugee_displacement")
    if involves_children:
        regimes.append("child_protection")
    if involves_disability:
        regimes.append("disability_rights")
    if involves_health:
        regimes.append("health_medical")
    if involves_personal_data or involves_precise_location:
        regimes.append("data_privacy")
    if "cyber" in clean_situation or "digital" in clean_situation or "network" in clean_situation:
        regimes.append("digital_cyber")
    if involves_cultural_property:
        regimes.append("cultural_property")
    if involves_environmental_harm:
        regimes.append("environment")
    if involves_sanctions:
        regimes.append("sanctions_humanitarian")

    ordered_regimes = tuple(dict.fromkeys(regimes))
    data = classify_humanitarian_data(
        health=involves_health,
        disability=involves_disability,
        child=involves_children,
        refugee_or_displacement_status=displacement,
        precise_civilian_location=involves_precise_location,
    )
    return {
        "accepted": True,
        "reason": "legal_review_envelope_prepared",
        "country": clean_country,
        "region": " ".join(region.split()).strip() if region else None,
        "situation_type": clean_situation,
        "armed_conflict_status": conflict,
        "ihl_classification_required": conflict == "unknown",
        "potentially_applicable_regimes": ordered_regimes,
        "primary_sources_verified": bool(primary_sources_verified),
        "domestic_law_currentness_verified": False,
        "treaty_status_currentness_verified": False,
        "sanctions_clearance": False,
        "legal_conclusion": False,
        "crime_determination": False,
        "conflict_classification_authority": False,
        "qualified_legal_review_required": True,
        "humanitarian_data": data,
        "law_of_the_jungle_applied_as_law": False,
        "law_of_the_jungle_role": "internal_oap_ethics_only",
        "human_authority_final": True,
    }


def humanitarian_legal_intelligence_status() -> dict[str, Any]:
    """Return Humanitarian Legal Intelligence architecture and truth boundaries."""

    ids = tuple(item["id"] for item in HUMANITARIAN_LEGAL_REGIMES)
    source_ids = tuple(item["id"] for item in PRIMARY_SOURCE_FAMILIES)
    data_levels = tuple(item["level"] for item in HUMANITARIAN_DATA_LEVELS)
    architecture_ready = (
        len(ids) == 17
        and len(ids) == len(set(ids))
        and len(source_ids) == len(set(source_ids))
        and data_levels == (0, 1, 2, 3, 4)
        and len(HUMANITARIAN_PRINCIPLES) == 4
        and len(OAP_LAW_OF_THE_JUNGLE) >= 10
    )
    return {
        "id": "humanitarian_legal",
        "name": "Humanitarian Legal Intelligence",
        "parent": "International Humanitarian Intelligence",
        "mode": "legal_routing_and_protection_review",
        "demo_mode": False,
        "architecture_ready": architecture_ready,
        "regime_count": len(HUMANITARIAN_LEGAL_REGIMES),
        "regimes": HUMANITARIAN_LEGAL_REGIMES,
        "humanitarian_principles": HUMANITARIAN_PRINCIPLES,
        "protected_person_contexts": PROTECTED_PERSON_CONTEXTS,
        "data_levels": HUMANITARIAN_DATA_LEVELS,
        "primary_source_families": PRIMARY_SOURCE_FAMILIES,
        "law_of_the_jungle": {
            "name": "OAP Law of the Jungle",
            "kind": "internal_ethics_and_resilience_code",
            "rules": OAP_LAW_OF_THE_JUNGLE,
            "legal_authority": False,
            "statutory_law": False,
            "international_law": False,
            "overrides_law_of_land": False,
        },
        "law_of_land_resolver": True,
        "country_required_for_domestic_resolution": True,
        "live_jurisdiction_database_ready": False,
        "live_treaty_status_feed_ready": False,
        "live_sanctions_feed_ready": False,
        "legal_advice_claim": False,
        "court_or_tribunal_claim": False,
        "conflict_classification_authority": False,
        "crime_determination_authority": False,
        "sanctions_clearance_authority": False,
        "independent_execute": False,
        "independent_approval": False,
        "civilian_only": True,
        "human_authority_final": True,
        "truth_boundary": (
            "Humanitarian Legal Intelligence can organise legal issues, protection duties, "
            "data sensitivity and source requirements. It cannot issue final jurisdiction-specific "
            "legal advice, classify an armed conflict authoritatively, determine crimes, clear a "
            "sanctions transaction, or treat OAP internal principles as state/international law."
        ),
    }
