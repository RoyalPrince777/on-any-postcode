from mission_control import humanitarian_legal_intelligence
from oap.smi.agi_core import AGICore


def test_humanitarian_legal_architecture_covers_full_regime_stack_without_authority():
    status = humanitarian_legal_intelligence.humanitarian_legal_intelligence_status()
    regime_ids = tuple(item["id"] for item in status["regimes"])

    assert status["name"] == "Humanitarian Legal Intelligence"
    assert status["parent"] == "International Humanitarian Intelligence"
    assert status["architecture_ready"] is True
    assert status["regime_count"] == 17
    assert regime_ids == (
        "ihl",
        "human_rights",
        "refugee_displacement",
        "international_criminal",
        "disaster_idrl",
        "law_of_land",
        "customary_international",
        "traditional_customary",
        "child_protection",
        "disability_rights",
        "health_medical",
        "data_privacy",
        "digital_cyber",
        "cultural_property",
        "environment",
        "sanctions_humanitarian",
        "humanitarian_principles",
    )
    assert status["law_of_land_resolver"] is True
    assert status["legal_advice_claim"] is False
    assert status["court_or_tribunal_claim"] is False
    assert status["conflict_classification_authority"] is False
    assert status["crime_determination_authority"] is False
    assert status["sanctions_clearance_authority"] is False
    assert status["independent_execute"] is False
    assert status["independent_approval"] is False
    assert status["human_authority_final"] is True


def test_law_of_jungle_is_internal_ethics_never_legal_authority():
    status = humanitarian_legal_intelligence.humanitarian_legal_intelligence_status()
    jungle = status["law_of_the_jungle"]

    assert jungle["kind"] == "internal_ethics_and_resilience_code"
    assert jungle["legal_authority"] is False
    assert jungle["statutory_law"] is False
    assert jungle["international_law"] is False
    assert jungle["overrides_law_of_land"] is False
    assert len(jungle["rules"]) >= 10


def test_law_of_land_requires_country_and_never_returns_final_legal_conclusion():
    blocked = humanitarian_legal_intelligence.resolve_humanitarian_legal_envelope(
        country="",
        situation_type="flood emergency",
    )
    prepared = humanitarian_legal_intelligence.resolve_humanitarian_legal_envelope(
        country="Ghana",
        region="Eastern Region",
        situation_type="flood emergency",
        primary_sources_verified=True,
    )

    assert blocked["accepted"] is False
    assert blocked["reason"] == "country_required_for_law_of_land"
    assert prepared["accepted"] is True
    assert "law_of_land" in prepared["potentially_applicable_regimes"]
    assert "human_rights" in prepared["potentially_applicable_regimes"]
    assert "disaster_idrl" in prepared["potentially_applicable_regimes"]
    assert prepared["legal_conclusion"] is False
    assert prepared["qualified_legal_review_required"] is True
    assert prepared["domestic_law_currentness_verified"] is False


def test_armed_conflict_hint_adds_ihl_customary_and_criminal_review_without_adjudication():
    result = humanitarian_legal_intelligence.resolve_humanitarian_legal_envelope(
        country="Ukraine",
        situation_type="civilian humanitarian response",
        armed_conflict_status="international",
        involves_health=True,
        involves_personal_data=True,
    )

    regimes = result["potentially_applicable_regimes"]
    assert "ihl" in regimes
    assert "customary_international" in regimes
    assert "international_criminal" in regimes
    assert "health_medical" in regimes
    assert "data_privacy" in regimes
    assert result["ihl_classification_required"] is False
    assert result["conflict_classification_authority"] is False
    assert result["crime_determination"] is False


def test_unknown_conflict_status_requires_classification_review():
    result = humanitarian_legal_intelligence.resolve_humanitarian_legal_envelope(
        country="Sudan",
        situation_type="humanitarian emergency",
        armed_conflict_status="unknown",
    )

    assert result["accepted"] is True
    assert result["ihl_classification_required"] is True
    assert result["conflict_classification_authority"] is False


def test_protection_dimensions_add_relevant_legal_review_domains():
    result = humanitarian_legal_intelligence.resolve_humanitarian_legal_envelope(
        country="United Kingdom",
        situation_type="cross-border humanitarian digital emergency",
        cross_border=True,
        displacement=True,
        involves_children=True,
        involves_disability=True,
        involves_health=True,
        involves_personal_data=True,
        involves_precise_location=True,
        involves_cultural_property=True,
        involves_environmental_harm=True,
        involves_sanctions=True,
    )

    regimes = result["potentially_applicable_regimes"]
    for regime in (
        "refugee_displacement",
        "child_protection",
        "disability_rights",
        "health_medical",
        "data_privacy",
        "digital_cyber",
        "cultural_property",
        "environment",
        "sanctions_humanitarian",
    ):
        assert regime in regimes
    assert result["sanctions_clearance"] is False
    assert result["humanitarian_data"]["level"] == 4
    assert result["humanitarian_data"]["public_default"] is False


def test_humanitarian_data_classifier_uses_highest_required_protection_level():
    public = humanitarian_legal_intelligence.classify_humanitarian_data()
    protected = humanitarian_legal_intelligence.classify_humanitarian_data(
        contact_or_household=True
    )
    sensitive = humanitarian_legal_intelligence.classify_humanitarian_data(
        health=True,
        child=True,
    )
    life_critical = humanitarian_legal_intelligence.classify_humanitarian_data(
        precise_civilian_location=True
    )

    assert public["level"] == 0
    assert protected["level"] == 2
    assert sensitive["level"] == 3
    assert sensitive["human_review_required"] is True
    assert life_critical["level"] == 4
    assert life_critical["precise_location_public"] is False


def test_agi_routes_humanitarian_legal_terms_to_canonical_specialist():
    route = AGICore().route(
        "Review Geneva Conventions, refugee law and the law of the land for civilian aid.",
        "GENERAL",
    )

    assert "international_humanitarian" in route["domain_ids"]
    assert "earth" in route["domain_ids"]
    assert "life" in route["domain_ids"]
    assert "humanitarian law" in route["matches"]["international_humanitarian"] or "geneva convention" in route["matches"]["international_humanitarian"]
    assert route["decision_authority"] is False
    assert route["execution_authority"] is False
    assert route["human_authority_final"] is True
