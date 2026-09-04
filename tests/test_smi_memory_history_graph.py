from __future__ import annotations

from oap.smi.knowledge_graph import graph_memory_items, status as graph_status
from oap.smi.memory_history import historical_memory_items, status as history_status
from oap.smi.memory_orchestrator import compose_text_memory, status as memory_status
from oap.smi.memory_sync import MemorySyncPacket, status as sync_status, validate_packet


def test_history_is_bounded_and_never_canonical_authority():
    snapshot = history_status()
    assert snapshot["ready"] is True
    assert snapshot["record_count"] >= 20
    assert snapshot["canonical_authority"] is False
    assert snapshot["latest_founder_correction_wins"] is True
    items = historical_memory_items("TECHNICAL", limit=4)
    assert len(items) == 4
    assert all(item.memory_id.startswith("history:") for item in items)
    assert all(item.summary.startswith("HISTORY ONLY") for item in items)


def test_graph_encodes_current_oap_relationships_without_people_profiles():
    snapshot = graph_status()
    assert snapshot["ready"] is True
    assert snapshot["node_count"] >= 30
    assert snapshot["edge_count"] >= 40
    assert snapshot["people_profiles_included"] is False
    items = graph_memory_items(
        "TECHNICAL",
        query="How does Matrix connect to OAP Maps and Guardian?",
        limit=4,
    )
    joined = " ".join(item.summary for item in items)
    assert "Matrix" in joined
    assert len(items) == 4


def test_orchestrator_keeps_21_cap_and_authority_order():
    snapshot = memory_status()
    assert snapshot["ready"] is True
    assert snapshot["context_cap"] == 21
    assert snapshot["canonical_budget"] == 10
    assert snapshot["historical_budget"] == 4
    assert snapshot["graph_budget"] == 3
    assert snapshot["dynamic_hrm_budget"] == 4
    assert snapshot["raw_chat_dump"] is False
    items = compose_text_memory(
        "TECHNICAL",
        query="Review Matrix OAP Maps architecture",
        dynamic=["one", "two", "three", "four", "five"],
    )
    assert len(items) == 21
    assert items[-4:] == ("two", "three", "four", "five")


def test_sync_contract_accepts_only_explicit_founder_approved_candidates():
    approved = validate_packet(
        MemorySyncPacket(
            source_kind="founder_decision",
            memory_class="CANONICAL_CANDIDATE",
            summary="Pulse is the canonical OAP feed language.",
            source_reference="founder-approved-chat-decision",
            founder_approved=True,
            supersedes=("Feed",),
            tags=("product-language",),
        )
    )
    assert approved["accepted_as_candidate"] is True
    assert approved["automatic_canonical_promotion"] is False
    assert approved["requires_audit"] is True
    assert approved["requires_human_authority"] is True
    assert approved["raw_chat_auto_ingestion"] is False

    rejected = validate_packet(
        MemorySyncPacket(
            source_kind="raw_chat_scrape",
            memory_class="CANONICAL_CANDIDATE",
            summary="Unreviewed transcript dump",
            source_reference="unknown",
            founder_approved=False,
        )
    )
    assert rejected["accepted_as_candidate"] is False
    assert "source_kind_not_allowed" in rejected["errors"]
    assert "founder_approval_required" in rejected["errors"]


def test_sync_status_is_truthful_about_external_transport_gap():
    snapshot = sync_status()
    assert snapshot["ready"] is True
    assert snapshot["direct_chatgpt_transport_connected"] is False
    assert snapshot["public_ingestion_endpoint"] is False
    assert snapshot["transport_state"] == "explicit_audited_import_required"
    assert snapshot["human_authority_final"] is True
