"""Fail-closed AEGIS heritage inventory regression tests."""
from oap.aegis.heritage import (
    APPROVED_NINE, EARLIER_HISTORICAL, CAPABILITIES,
    get_capability, inventory_status,
)

def test_preserves_distinct_historical_names_without_duplicate_parent():
    assert len(APPROVED_NINE) == 9
    assert len(EARLIER_HISTORICAL) == 4
    assert len(CAPABILITIES) == 13
    assert len({item.name for item in CAPABILITIES}) == 13
    assert "AEGIS" not in {item.name for item in CAPABILITIES}

def test_no_capability_receives_runtime_authority():
    assert all(not item.execution_enabled for item in CAPABILITIES)
    assert all(not item.runtime_verified for item in CAPABILITIES)

def test_unknown_and_non_string_fail_closed():
    assert get_capability("new unknown agent") is None
    assert get_capability("") is None
    assert get_capability(None) is None

def test_historical_labels_not_silently_promoted():
    for name in EARLIER_HISTORICAL:
        item = get_capability(name)
        assert item is not None
        assert item.lineage == "earlier_historical_unreconciled"

def test_status_does_not_fabricate_completion():
    status = inventory_status()
    assert status["approved_design_count"] == 9
    assert status["unreconciled_historical_count"] == 4
    assert status["runtime_verified_count"] == 0
    assert status["runtime_completion_percent"] is None
    assert status["execution_enabled"] is False

def test_all_fourteen_names_have_scoped_responsibilities():
    from oap.aegis.heritage import PARENT_ORGAN, PARENT_RESPONSIBILITY
    assert PARENT_ORGAN == "AEGIS"
    assert PARENT_RESPONSIBILITY
    assert len(CAPABILITIES) + 1 == 14
    assert all(item.proposed_responsibility.strip() for item in CAPABILITIES)

def test_design_metadata_cannot_be_mistaken_for_live_runtime():
    status = inventory_status()
    assert status["historical_named_components"] == 14
    assert status["responsibilities_are_proposals"] is True
    assert status["runtime_completion_percent"] is None
    assert status["execution_enabled"] is False
