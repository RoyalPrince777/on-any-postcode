from __future__ import annotations

from oap.smi.founder_memory_channel import synced_memory_items
from oap.smi.research_intelligence import CAPABILITY_IDS, RESEARCH_STAGES, depth_for_complexity
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
