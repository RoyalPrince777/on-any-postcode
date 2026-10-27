"""Founder Agents HQ HTTP boundary: real Flask routing, mocked model only."""
import app as app_module
from mission_control import smi_chat_runtime, web_security


def _client(monkeypatch, founder=True):
    monkeypatch.setattr(web_security, "current_authenticated_user", lambda: {
        "id": "11111111-1111-4111-8111-111111111111", "name": "Founder",
    })
    monkeypatch.setattr(web_security, "private_authority_allowed", lambda user: founder)
    client = app_module.app.test_client()
    with client.session_transaction() as session:
        session[web_security.CSRF_SESSION_KEY] = "a" * 48
    return client


def test_hq_endpoint_rejects_non_founder(monkeypatch):
    client = _client(monkeypatch, founder=False)
    assert client.post(
        "/mission/organiser/agents-hq/chat",
        json={"message": "hello"}, headers={"X-OAP-CSRF": "a" * 48}
    ).status_code == 403


def test_hq_endpoint_requires_csrf_before_inference(monkeypatch):
    client = _client(monkeypatch)
    def forbidden(*args, **kwargs):
        raise AssertionError("No inference without CSRF")
    monkeypatch.setattr(smi_chat_runtime, "chat", forbidden)
    response = client.post("/mission/organiser/agents-hq/chat", json={"message": "hello"})
    assert response.status_code == 403


def test_hq_endpoint_uses_session_identity_and_labels_smi(monkeypatch):
    client = _client(monkeypatch)
    seen = []
    def fake_chat(message, identity_id, display_name, conversation_id=None):
        seen.append((message, identity_id, display_name, conversation_id))
        return {"response": "reviewed response", "conversation_id": "c-1"}
    monkeypatch.setattr(smi_chat_runtime, "chat", fake_chat)
    response = client.post(
        "/mission/organiser/agents-hq/chat",
        json={"message": "Founder question", "identity_id": "FAKE", "conversation_id": "c-1"},
        headers={"X-OAP-CSRF": "a" * 48},
    )
    assert response.status_code == 200
    assert seen == [("Founder question", "11111111-1111-4111-8111-111111111111", "Founder", "c-1")]
    result = response.get_json()
    assert result["reply_source"] == "existing_governed_smi_runtime"
    assert result["individual_agent_reply_verified"] is False
    assert result["execution_authority_expanded"] is False
    assert response.headers["Cache-Control"] == "no-store"
