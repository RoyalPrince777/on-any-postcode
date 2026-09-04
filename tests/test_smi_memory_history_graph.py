from __future__ import annotations

from mission_control import smi_chat_runtime
from oap.smi.founder_memory_channel import status as founder_channel_status
from oap.smi.founder_memory_channel import synced_memory_items
from oap.smi.knowledge_graph import graph_memory_items
from oap.smi.knowledge_graph import status as graph_status
from oap.smi.memory_history import historical_memory_items
from oap.smi.memory_history import status as history_status
from oap.smi.memory_orchestrator import compose_text_memory
from oap.smi.memory_orchestrator import status as memory_status
from oap.smi.memory_sync import MemorySyncPacket, validate_packet
from oap.smi.memory_sync import status as sync_status


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


def test_founder_memory_channel_is_real_audited_transport_not_raw_chat_sync():
    snapshot = founder_channel_status()
    assert snapshot["ready"] is True
    assert snapshot["github_audited_transport_connected"] is True
    assert snapshot["direct_chatgpt_http_connected"] is False
    assert snapshot["always_on_raw_chat_sync"] is False
    assert snapshot["packet_count"] >= 5
    assert snapshot["rejected_packet_count"] == 0
    assert snapshot["latest_relevant_founder_packet_wins_ties"] is True
    assert snapshot["automatic_canonical_promotion"] is False
    items = synced_memory_items(
        "TECHNICAL",
        query="Kimi Qwen swarm subagents multimodal spatial capability expansion",
        limit=3,
    )
    assert len(items) == 3
    joined = " ".join(item.summary for item in items)
    assert "scale-out swarm" in joined
    assert "Qwen" in joined or "Kimi" in joined
    assert all(item.memory_id.startswith("founder-sync:") for item in items)
    assert all(item.summary.startswith("FOUNDER-APPROVED SYNC CONTEXT") for item in items)


def test_orchestrator_keeps_21_cap_and_authority_order():
    snapshot = memory_status()
    assert snapshot["ready"] is True
    assert snapshot["context_cap"] == 21
    assert snapshot["canonical_budget"] == 10
    assert snapshot["historical_budget"] == 3
    assert snapshot["graph_budget"] == 2
    assert snapshot["founder_sync_budget"] == 3
    assert snapshot["dynamic_hrm_budget"] == 3
    assert snapshot["github_memory_channel_connected"] is True
    assert snapshot["direct_chatgpt_http_connected"] is False
    assert snapshot["raw_chat_dump"] is False
    items = compose_text_memory(
        "TECHNICAL",
        query="Review Matrix OAP Maps architecture and AI capability fabric",
        dynamic=["one", "two", "three", "four", "five"],
    )
    assert len(items) == 21
    assert items[-3:] == ("three", "four", "five")
    assert any(item.startswith("FOUNDER-APPROVED SYNC CONTEXT") for item in items)


def test_live_smi_provider_receives_all_governed_memory_layers():
    items = smi_chat_runtime._canonical_provider_memory(
        {"task_type": "TECHNICAL"},
        ["old HRM", "recent HRM"],
        query="Explain Matrix OAP Maps Guardian and AI capability fabric",
    )
    assert len(items) <= 21
    assert any(item.startswith("HISTORY ONLY") for item in items)
    assert any(item.startswith("RELATIONSHIP") for item in items)
    assert any(item.startswith("FOUNDER-APPROVED SYNC CONTEXT") for item in items)
    assert items[-2:] == ["old HRM", "recent HRM"]
    assert not any("raw chat dump" in item.casefold() for item in items)


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


def test_sync_status_remains_truthful_about_direct_transport_gap():
    snapshot = sync_status()
    assert snapshot["ready"] is True
    assert snapshot["direct_chatgpt_transport_connected"] is False
    assert snapshot["public_ingestion_endpoint"] is False
    assert snapshot["transport_state"] == "explicit_audited_import_required"
    assert snapshot["human_authority_final"] is True
