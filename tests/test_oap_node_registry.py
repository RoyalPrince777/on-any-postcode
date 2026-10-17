from datetime import datetime, timedelta, timezone

import pytest

from mission_control.oap_node_registry import NodeRecord, NodeRegistry


def test_unknown_node_fails_closed():
    with pytest.raises(KeyError, match="unregistered_node"):
        NodeRegistry().inspect(node_id="unknown")


def test_identity_required_and_duplicates_rejected():
    node = NodeRecord("home", "android", "fingerprint")
    with pytest.raises(ValueError, match="duplicate_node_id"):
        NodeRegistry((node, node))
    with pytest.raises(ValueError, match="node_identity_required"):
        NodeRegistry((NodeRecord("", "android", "fingerprint"),))


def test_timestamp_is_not_health_proof():
    registry = NodeRegistry((NodeRecord("home", "android", "fingerprint"),))
    assert registry.inspect(node_id="home")["status"] == "unverified"
    assert registry.inspect(node_id="home", observed_at=datetime.now(timezone.utc))["status"] == "evidence_pending"
    assert registry.inspect(
        node_id="home", observed_at=datetime.now(timezone.utc) - timedelta(hours=1)
    )["status"] == "stale"
