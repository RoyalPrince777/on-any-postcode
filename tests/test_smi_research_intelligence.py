from __future__ import annotations

from datetime import datetime, timezone

import pytest

from oap.smi.founder_memory_channel import synced_memory_items
from oap.smi.research_intelligence import (
    CAPABILITY_IDS,
    RESEARCH_STAGES,
    assess_financial_observation,
    depth_for_complexity,
)
from oap.smi.research_intelligence import status as research_status


def test_research_intelligence_is_specialist_cluster_not_eighth_world():
    snapshot = research_status()
    assert snapshot["ready"] is True
    assert snapshot["specialist_cluster"] is True
    assert snapshot["intelligence_world"] is False
    assert snapshot["creates_eighth_world"] is False
    assert snapshot["human_authority_final"] is True
    assert snapshot["guardian_required"] is True
    assert snapshot["hrm_audit_required"] is True


def test_research_intelligence_uses_existing_3_7_21_depth_model():
    assert depth_for_complexity("quick") == 3
    assert depth_for_complexity("standard") == 7
    assert depth_for_complexity("deep") == 21
    assert len(RESEARCH_STAGES) == 7


def test_research_cluster_reuses_existing_governed_capabilities():
    required = {
        "cited_live_research",
        "parallel_retrieval",
        "evidence_first",
        "long_context_synthesis",
        "multi_expert_synthesis",
        "gap_adversarial_review",
        "memory_reconstruction",
    }
    assert required <= set(CAPABILITY_IDS)
    snapshot = research_status()
    assert snapshot["primary_sources_preferred"] is True
    assert snapshot["claim_source_linking"] is True
    assert snapshot["contradiction_detection"] is True
    assert snapshot["citation_fabrication_allowed"] is False
    assert snapshot["consequential_execution_authority"] is False


def test_founder_memory_channel_can_retrieve_research_intelligence_decision():
    items = synced_memory_items(
        "TECHNICAL",
        query="Research Intelligence evidence provenance verification sources",
        limit=3,
    )
    joined = " ".join(item.summary for item in items)
    assert "Research Intelligence" in joined
    assert "not an eighth Intelligence World" in joined


# CC21: these observations are entirely local test fixtures, not market feeds.

NOW = datetime(2026, 9, 30, 12, 0, tzinfo=timezone.utc)
TRUSTED_SOURCES = {"approved research source": {"research_use_permitted": True, "verified": True, "source_class": "reputable_secondary", "instruments": ("SAMPLE",)}}


def _financial_observation():
    return {
        "source": "approved research source",
        "source_class": "reputable_secondary",
        "research_use_permitted": True,
        "claim_supported": True,
        "observed_or_inferred": "observed",
        "instrument": "SAMPLE",
        "value": "12.34",
        "published_at": "2026-09-30T11:49:00Z",
        "observed_at": "2026-09-30T11:50:00Z",
        "retrieved_at": "2026-09-30T11:51:00Z",
    }


def test_cc21_valid_observation_remains_research_only():
    decision = assess_financial_observation(_financial_observation(), now=NOW, trusted_sources=TRUSTED_SOURCES)
    assert decision["usable_for_research"] is True
    assert decision["reasons"] == ()
    assert decision["read_only"] is True
    assert decision["trade_signal"] is False
    assert decision["execution_allowed"] is False
    assert decision["ledger_write_allowed"] is False
    assert decision["human_authority_final"] is True


@pytest.mark.parametrize(("field", "value", "reason"), (
    ("source", "", "missing_source"),
    ("source_class", "made_up", "invalid_source_class"),
    ("source_class", "community_or_social_signal", "social_signal_not_a_verified_quote"),
    ("claim_supported", False, "claim_not_verified"),
    ("observed_or_inferred", "inferred", "not_a_direct_observation"),
    ("instrument", "", "missing_instrument"),
    ("value", "NaN", "invalid_quote"),
    ("value", "-1", "invalid_quote"),
    ("value", "0", "invalid_quote"),
    ("value", "bad", "invalid_quote"),
    ("observed_at", "2026-09-30T11:50:00", "invalid_observed_at"),
    ("observed_at", "2026-09-30T11:30:00Z", "stale_observation"),
    ("retrieved_at", "2026-09-30T12:02:00Z", "inconsistent_or_future_timestamps"),
))
def test_cc21_unproved_or_stale_observations_fail_closed(field, value, reason):
    observation = _financial_observation()
    observation[field] = value
    if reason == "stale_observation":
        # Maintain chronological validity while making the quote stale.
        observation["published_at"] = "2026-09-30T11:29:00Z"
    decision = assess_financial_observation(observation, now=NOW, trusted_sources=TRUSTED_SOURCES)
    assert decision["usable_for_research"] is False
    assert reason in decision["reasons"]
    assert decision["execution_allowed"] is False
    assert decision["ledger_write_allowed"] is False


@pytest.mark.parametrize("field", (
    "trade_action", "auto_execute", "payment_instruction", "ledger_entry",
    "win_rate", "profit_loss", "guaranteed_return",
))
def test_cc21_quote_cannot_launder_trading_or_performance_claims(field):
    observation = _financial_observation()
    observation[field] = "some value"
    decision = assess_financial_observation(observation, now=NOW, trusted_sources=TRUSTED_SOURCES)
    assert decision["usable_for_research"] is False
    assert "execution_or_performance_claim_in_quote" in decision["reasons"]


def test_cc21_requires_aware_evaluation_clock():
    with pytest.raises(ValueError, match="timezone-aware"):
        assess_financial_observation(_financial_observation(), now=NOW.replace(tzinfo=None))


def test_cc21_never_changes_canonical_sika_ownership():
    from oap.smi.state_ownership_registry import owner_for
    assert owner_for("value").owner_component == "sika"
    assert owner_for("audit_evidence").owner_component == "oap_data"


def test_cc21_missing_trusted_registry_fails_closed():
    result = assess_financial_observation(_financial_observation(), now=NOW)
    assert result["usable_for_research"] is False
    assert "untrusted_source" in result["reasons"]


def test_cc21_source_registry_controls_permission_and_coverage():
    observation = _financial_observation()
    for change, expected in (
        ({"research_use_permitted": False}, "research_permission_not_proven"),
        ({"verified": False}, "source_not_verified"),
        ({"source_class": "first_party_or_official"}, "source_class_mismatch"),
        ({"instruments": ("OTHER",)}, "instrument_not_authorised"),
    ):
        record = {**TRUSTED_SOURCES["approved research source"], **change}
        result = assess_financial_observation(
            observation, now=NOW, trusted_sources={"approved research source": record},
        )
        assert result["usable_for_research"] is False
        assert expected in result["reasons"]
