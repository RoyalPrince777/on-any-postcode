from pathlib import Path

from mission_control import smi_chat_runtime, web_security


def _session_security(client):
    identity_id = "11111111-1111-4111-8111-111111111111"
    token = "test-founder-final-csrf-token-1234567890"
    with client.session_transaction() as session:
        session[web_security.IDENTITY_SESSION_KEY] = identity_id
        session[web_security.CSRF_SESSION_KEY] = token
    return identity_id, token


def test_founder_final_chat_route_requires_csrf(client, monkeypatch):
    _session_security(client)
    called = False

    def fake_record(*args, **kwargs):
        nonlocal called
        called = True
        del args, kwargs

    monkeypatch.setattr(smi_chat_runtime, "record_founder_final", fake_record)

    response = client.post(
        "/mission/chat/founder-final",
        json={"conversation_id": "22222222-2222-4222-8222-222222222222"},
    )

    assert response.status_code == 403
    assert called is False


def test_founder_final_chat_route_records_zero_execution_receipt(client, monkeypatch):
    identity_id, token = _session_security(client)
    observed = {}

    def fake_record(current_identity, conversation_id, decision):
        observed.update(
            identity=current_identity,
            conversation_id=conversation_id,
            decision=decision,
        )
        return {
            "status": "recorded",
            "conversation_id": conversation_id,
            "request_id": "33333333-3333-4333-8333-333333333333",
            "decision": "APPROVED",
            "receipt_id": "44444444-4444-4444-8444-444444444444",
            "signature_verified": True,
            "authority_level": 0,
            "response": "Founder Final recorded.",
            "execution_granted": False,
            "human_authority_final": True,
        }

    monkeypatch.setattr(smi_chat_runtime, "record_founder_final", fake_record)

    response = client.post(
        "/mission/chat/founder-final",
        json={"conversation_id": "22222222-2222-4222-8222-222222222222"},
        headers={"X-OAP-CSRF": token},
    )
    payload = response.get_json()

    assert response.status_code == 200
    assert observed == {
        "identity": identity_id,
        "conversation_id": "22222222-2222-4222-8222-222222222222",
        "decision": "APPROVED",
    }
    assert payload["signature_verified"] is True
    assert payload["authority_level"] == 0
    assert payload["execution_granted"] is False
    assert payload["human_authority_final"] is True


def test_live_smi_green_command_uses_founder_final_endpoint_not_stream():
    root = Path(__file__).parents[1]
    controller = (root / "mission_control" / "static" / "smi_canonical_controller.js").read_text()
    template = (root / "mission_control" / "templates" / "ollama_chat.html").read_text()

    assert "founderFinalUrl:" in template
    assert "if(text==='🟢'&&!hasImage&&!hasAttachment&&!codeMode)" in controller
    assert "decision:'APPROVED'" in controller
    assert "execution remains locked" in controller


def test_continuation_query_excludes_founder_final_decisions():
    root = Path(__file__).parents[1]
    core = (root / "mission_control" / "smi_chat_runtime_core.py").read_text()

    assert "JOIN smi_judgement_reviews j ON j.request_id=m.request_id" in core
    assert "AND j.human_decision IS NULL" in core
