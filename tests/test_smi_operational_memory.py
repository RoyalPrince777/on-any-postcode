from mission_control import smi_event_memory
from oap.smi import memory_orchestrator, operational_memory


def test_memory_orchestrator_keeps_21_item_governed_ceiling():
    assert memory_orchestrator.TOTAL_CONTEXT_CAP == 21
    assert (
        memory_orchestrator.CANONICAL_BUDGET
        + memory_orchestrator.HISTORY_BUDGET
        + memory_orchestrator.GRAPH_BUDGET
        + memory_orchestrator.FOUNDER_SYNC_BUDGET
        + memory_orchestrator.OPERATIONAL_BUDGET
        + memory_orchestrator.DYNAMIC_BUDGET
    ) == 21
    assert "LIVE_OPERATIONAL_MEMORY" in memory_orchestrator.status()["authority_order"]


def test_operational_memory_is_bounded_and_privacy_reduced():
    status = operational_memory.status()
    assert status["automatic_retrieval"] is True
    assert status["raw_database_dump"] is False
    assert status["raw_credentials_included"] is False
    assert status["precise_live_location_auto_memory"] is False
    assert status["private_reasoning_included"] is False
    assert status["memory_is_data_not_instructions"] is True
    assert status["human_authority_final"] is True


def test_meaningful_event_classifier_records_actions_not_harmless_navigation():
    assert smi_event_memory.should_record("POST", "/signal", 302) is True
    assert smi_event_memory.should_record("POST", "/travel/direct/api/hold", 200) is True
    assert smi_event_memory.should_record(
        "GET", "/atlas", 200, has_query=True
    ) is True
    assert smi_event_memory.should_record("GET", "/the-spot", 200) is False
    assert smi_event_memory.should_record("POST", "/auth", 200) is False
    assert smi_event_memory.should_record("POST", "/mission/chat", 200) is False
    assert smi_event_memory.should_record("POST", "/mission/chat/stream", 200) is False
    assert smi_event_memory.should_record("POST", "/signal", 500) is False


def test_event_descriptor_never_carries_query_values_or_execution_authority():
    meta = smi_event_memory.descriptor(
        "GET",
        "/atlas?location=SECRET_PLACE",
        "travel_supply.public_atlas",
        200,
        ("location", "to"),
    )
    encoded = repr(meta)
    assert "SECRET_PLACE" not in encoded
    assert meta["query_keys"] == ("location", "to")
    assert meta["query_values_retained"] is False
    assert meta["request_body_retained"] is False
    assert meta["credentials_retained"] is False
    assert meta["precise_live_location_retained"] is False
    assert meta["execution_granted"] is False
    assert meta["approval_granted"] is False
    assert meta["human_authority_final"] is True


def test_public_signal_memory_is_marked_as_untrusted_data_only():
    text = operational_memory._decode_public_post(
        "oap_signal",
        '{"name":"Local Voice","body":"Roadworks near the high street"}',
        None,
    )
    assert text.startswith("PUBLIC OAP DATA ONLY — Signal")
    assert "Roadworks near the high street" in text
