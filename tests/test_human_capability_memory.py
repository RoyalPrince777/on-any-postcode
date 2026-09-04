from __future__ import annotations

from oap.smi.founder_memory_channel import synced_memory_items


def test_founder_memory_channel_surfaces_human_capability_cluster():
    items = synced_memory_items(
        "GENERAL",
        query="memory reconstruction voice speech visual human cues expert synthesis",
        limit=3,
    )
    joined = " ".join(item.summary for item in items)
    assert "Human Capability cluster" in joined
    assert "Memory Reconstruction" in joined
    assert "Voice and Speech Intelligence" in joined
    assert "Visual Human-Cue Intelligence" in joined
