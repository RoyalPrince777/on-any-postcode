from __future__ import annotations

import json

from mission_control import config, ollama_chat


def test_smi_chat_projection_preserves_provider_and_authority_boundaries():
    projection = ollama_chat.get_public_ollama_chat()

    assert projection["provider"]["id"] == "openai"
    assert projection["provider"]["model"] == "gpt-5-mini"
    assert projection["provider"]["scope"] == "Governed cloud provider"
    assert projection["provider"]["agent"] is False
    assert projection["provider"]["authority"] is False
    assert projection["readiness"]["composer_enabled"] is False
    assert projection["execution"] == "Recommendation only"
    assert projection["human_authority"]["status"] == "Final approval required"


def test_smi_chat_dashboard_is_governed_and_does_not_create_local_database(
    client, tmp_path, monkeypatch
):
    database_path = tmp_path / "ollama-chat.db"
    monkeypatch.setattr(config, "OAP_DATABASE_PATH", str(database_path))

    response = client.get("/mission/ollama")
    page = response.get_data(as_text=True)

    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    assert "Personal SMI" in page
    assert "Private Founder intelligence" in page
    assert "Message OAP Mind" in page
    assert "Real-time · Streamed" in page
    assert "Durable · Conversation history" in page
    assert "Code proposal" in page
    assert "apply and deploy remain locked" in page
    assert 'method="post"' not in page.lower()
    assert client.post("/mission/ollama").status_code == 405
    assert client.post("/mission/ollama/send").status_code == 404
    assert not database_path.exists()


def test_ollama_chat_get_never_calls_provider(client, monkeypatch):
    def fail_if_called(*args, **kwargs):
        raise AssertionError("GET dashboard must not contact Ollama")

    monkeypatch.setattr("urllib.request.OpenerDirector.open", fail_if_called)

    assert client.get("/mission/ollama").status_code == 200


def test_non_loopback_local_fallback_is_not_reported_ready(monkeypatch):
    monkeypatch.setattr(config, "OLLAMA_URL", "https://example.invalid/api/generate")

    projection = ollama_chat.get_public_ollama_chat()

    assert projection["readiness"]["local_fallback_loopback"] is False
    assert projection["readiness"]["composer_enabled"] is False


def test_public_ollama_projection_is_redacted_and_uses_intelligence_terminology():
    serialized = json.dumps(ollama_chat.get_public_ollama_chat()).lower()

    for private_key in ("secret", "password", "token", "totp", "correlation_id"):
        assert private_key not in serialized
    assert "council" not in serialized
    assert '"kaa"' not in serialized
    assert '"execute"' not in serialized
