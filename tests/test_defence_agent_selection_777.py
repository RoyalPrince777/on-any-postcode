"""Fail-closed tests for registry-grounded defence agent candidate selection."""
import pytest

from mission_control import defence_agent_selection_777 as selection


def test_denies_unverified_founder():
    with pytest.raises(PermissionError):
        selection.select_read_only("strategic", guardian_verified=True)


def test_denies_unverified_guardian():
    with pytest.raises(PermissionError):
        selection.select_read_only("strategic", founder_verified=True)


def test_unknown_division_denied():
    with pytest.raises(ValueError):
        selection.select_read_only("weapons", founder_verified=True, guardian_verified=True)


@pytest.mark.parametrize("division", tuple(selection.PREFERENCES))
def test_all_divisions_never_activate(division):
    result = selection.select_read_only(division, founder_verified=True, guardian_verified=True)
    assert result["assignment_active"] is False
    assert result["execution_granted"] is False
    assert result["hrm_receipt_persisted"] is False
    assert all(not agent["passport_verified"] and not agent["runtime_connected"] for agent in result["candidates"])
