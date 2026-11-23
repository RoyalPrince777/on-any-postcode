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


def test_server_enforces_first_party_regardless_of_client_source(client, csrf, monkeypatch):
    import app as app_module

    seen = []
    def fake_ask(message, *, rate_key, history=None, first_party_only=False):
        seen.append(first_party_only)
        return {
            "answer": "bounded",
            "brain": "SMI",
            "smi_surface": "public",
            "execution_authority": False,
            "first_party_only": first_party_only,
        }

    monkeypatch.setattr(app_module.public_studio_runtime, "ask", fake_ask)
    headers = {"X-OAP-CSRF": csrf["csrf_token"]}
    for route, source, should_be_first_party in (
        ("/koradaso/chat", "studio", True),
        ("/koradaso/chat", None, True),
        ("/studio/chat", "koradaso", True),
        ("/studio/chat", "studio", False),
    ):
        response = client.post(
            route,
            json={"message": "Hello", "source": source},
            headers=headers,
        )
        assert response.status_code == 200
        assert response.get_json()["first_party_only"] is should_be_first_party
        assert response.get_json()["execution_authority"] is False
        assert response.headers["Cache-Control"] == "no-store"
    assert seen == [True, True, True, False]


def test_koradaso_compass_posts_to_server_enforced_chat(client):
    page = client.get("/studio?source=koradaso").get_data(as_text=True)
    assert "fetch('/koradaso/chat',options)" in page
    assert "fetch('/studio/chat',options)" in page
    assert "source:koradasoMode?'koradaso':'studio'" in page
