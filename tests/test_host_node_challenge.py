"""Node-bound challenge verification must fail closed and never claim VPS ownership."""
import hashlib
import hmac

from mission_control import home_node_bridge as bridge
from mission_control import oap_host


def _sign(node_id, nonce, secret):
    return hmac.new(secret.encode(), (node_id + "\n" + nonce).encode(), hashlib.sha256).hexdigest()


def test_node_challenge_authentic_single_use(monkeypatch):
    secret = "private-bridge-secret-" * 3
    monkeypatch.setenv("OAP_HOME_NODE_BRIDGE_SECRET", secret)
    issued = bridge.issue_node_challenge("node-1")
    assert issued is not None
    signature = _sign("node-1", issued["challenge"], secret)
    assert bridge.verify_node_challenge("node-1", issued["challenge"], signature) is True
    assert bridge.verify_node_challenge("node-1", issued["challenge"], signature) is False
    assert oap_host.status()["runtime_ready"] is False


def test_node_challenge_rejects_wrong_identity_and_replay(monkeypatch):
    secret = "private-bridge-secret-" * 3
    monkeypatch.setenv("OAP_HOME_NODE_BRIDGE_SECRET", secret)
    nonce = bridge.issue_node_challenge("node-1")["challenge"]
    assert bridge.verify_node_challenge("node-2", nonce, _sign("node-2", nonce, secret)) is False
    assert bridge.verify_node_challenge("node-1", nonce, _sign("node-1", nonce, secret)) is False


def test_node_challenge_rejects_forgery_and_expiry(monkeypatch):
    secret = "private-bridge-secret-" * 3
    monkeypatch.setenv("OAP_HOME_NODE_BRIDGE_SECRET", secret)
    nonce = bridge.issue_node_challenge("node-1")["challenge"]
    assert bridge.verify_node_challenge("node-1", nonce, "0" * 64) is False
    monkeypatch.setattr(bridge.time, "monotonic", lambda: 100.0)
    nonce = bridge.issue_node_challenge("node-1")["challenge"]
    monkeypatch.setattr(bridge.time, "monotonic", lambda: 131.0)
    assert bridge.verify_node_challenge("node-1", nonce, _sign("node-1", nonce, secret)) is False


def test_node_challenge_requires_configuration_and_valid_identity(monkeypatch):
    monkeypatch.delenv("OAP_HOME_NODE_BRIDGE_SECRET", raising=False)
    assert bridge.issue_node_challenge("") is None
    nonce = bridge.issue_node_challenge("node-1")["challenge"]
    assert bridge.verify_node_challenge("node-1", nonce, "anything") is False
