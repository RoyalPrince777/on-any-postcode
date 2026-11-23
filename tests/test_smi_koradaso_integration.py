"""Isolated cross-surface integration proof. No deployment certification."""
import pytest
from mission_control import oap_inference_gateway as gateway


def test_public_entry_and_private_auth_boundaries(anonymous_client):
    root = anonymous_client.get("/", follow_redirects=False)
    assert root.status_code == 302
    assert root.headers["Location"].endswith("/koradaso")
    for path in ("/koradaso", "/studio?source=koradaso"):
        response = anonymous_client.get(path)
        assert response.status_code == 200
        assert response.headers.get("Cache-Control") == "no-store"
        assert response.headers.get("X-Frame-Options") == "DENY"
    assert anonymous_client.get("/mission/ollama").status_code == 302
    assert anonymous_client.post("/mission/chat/stream", json={"message": "test"}).status_code == 401
    assert anonymous_client.get("/mission/smi/alliances/status").status_code == 401
    assert anonymous_client.post(
        "/studio/chat", json={"source": "koradaso", "message": "hello"}
    ).status_code == 403


def test_founder_chat_same_origin_and_csrf_gate(client):
    response = client.get("/mission/ollama")
    assert response.status_code == 200
    assert "no-store" in response.headers.get("Cache-Control", "")
    assert response.headers.get("X-Frame-Options") == "SAMEORIGIN"
    assert "frame-ancestors 'self'" in response.headers["Content-Security-Policy"]
    assert "alliancesUrl:" in response.get_data(as_text=True)
    assert client.post("/mission/chat/stream", json={"message": "test"}).status_code == 403


def test_koradaso_disallows_compatibility_fallback(monkeypatch):
    called = {"compatibility": 0}
    def offline(*_args, **_kwargs):
        raise RuntimeError("inference_unavailable")
    def compatibility(*_args, **_kwargs):
        called["compatibility"] += 1
        return "This is not first-party inference"
    monkeypatch.setattr(gateway, "_call_local_public", offline)
    monkeypatch.setattr(gateway, "_call_bridge_public", offline)
    monkeypatch.setattr(gateway, "FALLBACK_ENABLED", True)
    monkeypatch.setattr(gateway, "OFFLINE_ONLY", False)
    with pytest.raises(RuntimeError, match="first_party_inference_required"):
        gateway.generate_public(compatibility, "Test", first_party_only=True)
    assert called["compatibility"] == 0


def test_non_loopback_local_inference_denied(monkeypatch):
    monkeypatch.setattr(gateway, "LOCAL_ENABLED", True)
    monkeypatch.setattr(gateway, "LOCAL_MODEL", "smallsmi")
    monkeypatch.setattr(gateway, "LOCAL_URL", "http://192.168.1.100:11434/api/chat")
    assert gateway._local_endpoint_allowed() is False
    with pytest.raises(RuntimeError, match="local_inference_disabled"):
        gateway._call_local_public("Test", None, None, code_mode=False)
