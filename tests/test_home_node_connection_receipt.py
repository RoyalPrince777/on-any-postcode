"""Fail-closed receipt checks; receipts are not self-hosting attestations."""

from mission_control import home_node_bridge as bridge


def test_receipt_is_single_use():
    receipt = bridge.issue_connection_receipt()["receipt"]
    assert bridge.consume_connection_receipt(receipt) is True
    assert bridge.consume_connection_receipt(receipt) is False


def test_missing_and_forged_receipts_rejected():
    assert bridge.consume_connection_receipt(None) is False
    assert bridge.consume_connection_receipt("") is False
    assert bridge.consume_connection_receipt("forged") is False


def test_expired_receipt_rejected(monkeypatch):
    monkeypatch.setattr(bridge.time, "monotonic", lambda: 100.0)
    receipt = bridge.issue_connection_receipt()["receipt"]
    monkeypatch.setattr(bridge.time, "monotonic", lambda: 131.0)
    assert bridge.consume_connection_receipt(receipt) is False
