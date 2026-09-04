from __future__ import annotations

import pytest
from flask import Flask

from mission_control import safe_signals, travel_supply_views


def test_safe_signals_doctrine_and_world_boundary(monkeypatch):
    monkeypatch.setattr(
        safe_signals,
        "schema_status",
        lambda: {
            "migration": safe_signals.SAFE_SIGNALS_MIGRATION_VERSION,
            "checksum": safe_signals.SAFE_SIGNALS_MIGRATION_CHECKSUM,
            "schema_ready": False,
            "tables": 0,
            "expected_tables": 5,
            "error": "pending",
        },
    )
    current = safe_signals.status()
    assert current["software_ready"] is True
    assert current["postcode_to_planet"] is True
    assert current["weather_preparation_not_fear"] is True
    assert current["official_civic_channels_only"] is True
    assert current["community_polls_binding"] is False
    assert current["legal_advice"] is False
    assert current["financial_advice"] is False
    assert current["political_manipulation"] is False
    assert current["fake_petitions"] is False
    assert current["youth_campaign_recruitment"] is False
    assert current["autonomous_action"] is False
    assert current["creates_intelligence_worlds"] is False
    assert current["creates_agents"] is False
    assert current["creates_brain"] is False
    assert current["human_authority_final"] is True


def test_schema_is_explicit_and_bounded():
    assert safe_signals.SAFE_SIGNALS_MIGRATION_VERSION == "0009_safe_signals_v03"
    assert safe_signals.SAFE_SIGNALS_TABLES == {
        "oap_world_signals",
        "oap_civic_voice_items",
        "oap_mentorship_guides",
        "oap_signal_corrections",
        "oap_signal_audit_logs",
    }
    assert len(safe_signals.SAFE_SIGNALS_MIGRATION_CHECKSUM) == 64
    with pytest.raises(RuntimeError, match="Explicit human approval"):
        safe_signals.init_schema()


def test_no_go_flags_fail_closed_before_database_access():
    for flag in (
        "legal_advice",
        "financial_advice",
        "binding_vote",
        "fake_signature",
        "pressure_campaign",
        "targets_individual",
        "precise_person_location",
        "youth_campaign_recruitment",
        "autonomous_action",
    ):
        with pytest.raises(PermissionError, match="safe_signals_no_go_boundary"):
            safe_signals._enforce_no_go_flags({flag: True})


def test_civic_voice_requires_official_non_binding_channel():
    store = safe_signals.SafeSignalsStore()
    payload = {
        "human_authority_approved": True,
        "official_channel": True,
        "non_binding": False,
    }
    with pytest.raises(PermissionError, match="official_non_binding_civic_channel_required"):
        store.create_civic_item(payload)


def test_youth_mentorship_must_be_youth_safe():
    store = safe_signals.SafeSignalsStore()
    payload = {
        "human_authority_approved": True,
        "audience": "YOUTH",
        "youth_safe": False,
    }
    with pytest.raises(PermissionError, match="youth_guide_must_be_youth_safe"):
        store.create_mentorship_guide(payload)


def test_civic_and_source_links_require_https():
    with pytest.raises(ValueError, match="source_url_must_be_https"):
        safe_signals._https("http://example.org/item", "source_url")
    assert safe_signals._https("https://example.org/item", "source_url").startswith(
        "https://"
    )


def test_public_safe_signal_routes_are_registered_without_breaking_travel():
    app = Flask(__name__)
    app.register_blueprint(travel_supply_views.bp)
    rules = {rule.rule for rule in app.url_map.iter_rules()}
    assert "/signals" in rules
    assert "/weather" in rules
    assert "/news-facts" in rules
    assert "/civic-voice" in rules
    assert "/mentorship" in rules
    assert "/travel/direct" in rules
    assert "/travel/api/catalogue" in rules
    assert "/travel/partner/api/offers" not in rules
    assert "/mission/safe-signals/status" in rules
