from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_bridge_is_outbound_only_and_secret_protected():
    bridge = (ROOT / "mission_control" / "home_node_bridge.py").read_text()
    views = (ROOT / "mission_control" / "home_node_views.py").read_text()
    worker = (ROOT / "scripts" / "oap_home_node_inference_worker.py").read_text()
    assert "OAP_HOME_NODE_BRIDGE_SECRET" in bridge
    assert "hmac.compare_digest" in bridge
    assert "public_ollama_required" in bridge
    assert '"outbound_https_poll"' in bridge
    assert "X-OAP-Home-Node-Token" in views
    assert "/home-node/jobs/next" in views
    assert "127.0.0.1:11434/api/chat" in worker
    assert "https://oap-smi.onrender.com/mission" in worker


def test_inference_gateway_routes_first_party_before_fallback():
    gateway = (ROOT / "mission_control" / "oap_inference_gateway.py").read_text()
    direct = gateway.index("text = _call_local")
    bridge = gateway.index("text = _call_bridge")
    fallback = gateway.index("return compatibility_engine")
    assert direct < bridge < fallback
    assert "first_party_inference_ready" in gateway
    assert "sovereign_inference_ready" in gateway
    assert "not FALLBACK_ENABLED" in gateway
