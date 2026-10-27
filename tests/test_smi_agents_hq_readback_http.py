"""Agents HQ read-back is scoped to the actual authenticated Founder."""
import app as app_module
from mission_control import smi_chat_runtime, web_security


def _client(monkeypatch, founder=True):
    monkeypatch.setattr(web_security, "current_authenticated_user", lambda: {
        "id": "11111111-1111-4111-8111-111111111111", "name": "Founder",
    })
    monkeypatch.setattr(web_security, "private_authority_allowed", lambda user: founder)
    return app_module.app.test_client()


def test_agents_hq_readback_refuses_non_founder(monkeypatch):
    client = _client(monkeypatch, founder=False)
    response = client.get("/mission/organiser/agents-hq/conversation/cccccccc-cccc-4ccc-8ccc-cccccccccccc")
    assert response.status_code == 403


def test_agents_hq_readback_uses_session_owner(monkeypatch):
    client = _client(monkeypatch)
    seen = []
    def read(identity_id, conversation_id):
        seen.append((identity_id, conversation_id))
        return {"conversation_id": conversation_id, "messages": []}
    monkeypatch.setattr(smi_chat_runtime, "get_conversation", read)
    cid = "cccccccc-cccc-4ccc-8ccc-cccccccccccc"
    response = client.get("/mission/organiser/agents-hq/conversation/" + cid)
    assert response.status_code == 200
    assert seen == [("11111111-1111-4111-8111-111111111111", cid)]
    result = response.get_json()
    assert result["source"] == "existing_owner_scoped_smi_store"
    assert result["individual_agent_sender_verified"] is False
    assert response.headers["Cache-Control"] == "no-store"


def test_agents_hq_readback_missing_conversation_is_not_leaked(monkeypatch):
    client = _client(monkeypatch)
    monkeypatch.setattr(smi_chat_runtime, "get_conversation",
                        lambda owner, cid: (_ for _ in ()).throw(ValueError("conversation_not_found")))
    result = client.get("/mission/organiser/agents-hq/conversation/cccccccc-cccc-4ccc-8ccc-cccccccccccc")
    assert result.status_code == 404
    assert "conversation_not_found" in result.get_json()["error"]
