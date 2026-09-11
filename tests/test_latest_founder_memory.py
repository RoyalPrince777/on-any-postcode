from oap.smi import latest_founder_memory, memory_orchestrator


def test_latest_founder_memory_contains_current_locked_rules():
    items = latest_founder_memory.latest_founder_memory_items()
    text = "\n".join(item.summary for item in items)
    assert "JOOG MEMORY" in text
    assert "no demo" in text
    assert "no fake green" in text
    assert "Kaa is completely excluded" in text
    assert "one canonical Send/Enter/Mic/Voice/Stop runtime" in text
    assert (
        latest_founder_memory.status()["revision"]
        == "2026-09-11-founder-parity"
    )


def test_latest_founder_memory_outranks_older_canonical_context():
    items = memory_orchestrator.compose_memory("GENERAL", limit=21)
    status = memory_orchestrator.status()
    assert items[0].task_type == "LATEST_FOUNDER_LOCK"
    assert items[0].memory_id.startswith("founder-lock:")
    assert status["authority_order"][0] == "LATEST_FOUNDER_LOCK"
    assert status["budget_total"] == 21


def test_latest_founder_memory_never_claims_raw_chat_or_private_reasoning_copy():
    status = latest_founder_memory.status()
    assert status["raw_chat_dump"] is False
    assert status["private_chain_of_thought_included"] is False
    assert status["credentials_or_secrets_included"] is False
    assert status["human_authority_final"] is True
