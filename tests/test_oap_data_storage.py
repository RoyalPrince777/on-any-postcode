"""OAP Data capacity admission contract."""
import pytest

from mission_control.oap_data_storage import StorageCapacity, admission


def test_unverified_capacity_fails_closed():
    assert admission(system="music", requested_bytes=1, capacity=None)["allowed"] is False
    assert admission(
        system="music", requested_bytes=1,
        capacity=StorageCapacity(1000, 0),
    )["reason"] == "capacity_unverified"


def test_measured_capacity_preserves_reserve():
    cap = StorageCapacity(1000, 300, measured=True)
    assert admission(system="music", requested_bytes=500, capacity=cap)["allowed"] is True
    assert admission(system="music", requested_bytes=501, capacity=cap)["allowed"] is False


def test_invalid_capacity_rejected():
    with pytest.raises(ValueError):
        StorageCapacity(10, 11, measured=True)
    with pytest.raises(ValueError):
        admission(system="unknown", requested_bytes=1, capacity=None)
    with pytest.raises(ValueError):
        admission(system="drive", requested_bytes=-1, capacity=None)
