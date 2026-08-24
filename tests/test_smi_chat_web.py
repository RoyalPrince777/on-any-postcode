from __future__ import annotations

import json

from mission_control import smi_chat_runtime, web_security


def _session_security(client):
    identity_id = "11111111-1111-4111-8111-111111111111"
    token = "test-chat-csrf-token-value-1234567890"
    with client.session_transaction() as current_session:
        current_session[web_security.IDENTITY_SESSION_KEY] = identity_id
        current_session[web_security.CSRF_SESSION_KEY] = token
    return identity_id, token


def test_chat_json_route_requires_csrf(client):
    response = client.post("/mission/chat", json={"message": "Review OAP."})

    assert response.status_code == 403
    assert response.get_json()["error"]["code"] == "csrf_failed"


def test_chat_stream_emits_real_events_and_complete_only_from_runtime(
    client, monkeypatch
):
    _, token = _session_security(client)

    def fake_events(*args, **kwargs):
        del args, kwargs
        yield {"type": "stage", "stage": "identity", "label": "Identity verified"}
        yield {"type": "delta", "delta": "OAP "}
        yield {"type": "delta", "delta": "ready"}
        yield {
            "type": "complete",
            "result": {"conversation_id": "conversation-1", "response": "OAP ready"},
        }

    monkeypatch.setattr(smi_chat_runtime, "chat_events", fake_events)

    response = client.post(
        "/mission/chat/stream",
        json={"message": "Review OAP."},
        headers={"X-OAP-CSRF": token},
    )
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert response.mimetype == "text/event-stream"
    assert "event: stage" in body
    assert '"delta":"OAP "' in body
    assert "event: complete" in body
    assert body.index("event: complete") > body.index('"delta":"ready"')


def test_conversation_routes_pass_only_the_signed_session_identity(
    client, monkeypatch
):
    identity_id, token = _session_security(client)
    observed: list[tuple[str, str]] = []

    monkeypatch.setattr(
        smi_chat_runtime,
        "list_conversations",
        lambda current_identity: [
            {
                "conversation_id": "conversation-1",
                "title": current_identity,
                "preview": "Private projection",
            }
        ],
    )

    def fake_get(current_identity, conversation_id):
        observed.append((current_identity, conversation_id))
        return {"conversation_id": conversation_id, "messages": []}

    def fake_delete(current_identity, conversation_id):
        observed.append((current_identity, conversation_id))
        return {"status": "deleted", "conversation_id": conversation_id}

    monkeypatch.setattr(smi_chat_runtime, "get_conversation", fake_get)
    monkeypatch.setattr(smi_chat_runtime, "delete_conversation", fake_delete)

    listed = client.get("/mission/conversations").get_json()["conversations"]
    loaded = client.get("/mission/conversations/conversation-1")
    deleted = client.delete(
        "/mission/conversations/conversation-1", headers={"X-OAP-CSRF": token}
    )

    assert listed[0]["title"] == identity_id
    assert loaded.status_code == 200
    assert deleted.status_code == 200
    assert observed == [
        (identity_id, "conversation-1"),
        (identity_id, "conversation-1"),
    ]


def test_conversation_delete_requires_csrf(client, monkeypatch):
    _session_security(client)
    called = False

    def fake_delete(*args):
        nonlocal called
        called = True
        del args

    monkeypatch.setattr(smi_chat_runtime, "delete_conversation", fake_delete)

    response = client.delete("/mission/conversations/conversation-1")

    assert response.status_code == 403
    assert called is False


def test_provider_requests_streaming_and_forwards_true_deltas(monkeypatch):
    captured = {}

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            del exc_type, exc, traceback

        def __iter__(self):
            events = (
                {"type": "response.output_text.delta", "delta": "OAP "},
                {"type": "response.output_text.delta", "delta": "ready"},
                {"type": "response.completed", "response": {}},
            )
            return iter(
                [f"data: {json.dumps(event)}\n\n".encode() for event in events]
            )

    def fake_urlopen(request, timeout):
        captured["payload"] = json.loads(request.data.decode())
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setenv("OPENAI_API_KEY", "test-provider-key")
    monkeypatch.setattr(smi_chat_runtime.urlrequest, "urlopen", fake_urlopen)
    deltas: list[str] = []

    result = smi_chat_runtime._provider(
        "Review OAP.", code_mode=True, on_delta=deltas.append
    )

    assert result == "OAP ready"
    assert deltas == ["OAP ", "ready"]
    assert captured["payload"]["stream"] is True
    assert captured["payload"]["max_output_tokens"] == 1200


def test_chat_event_bridge_marks_complete_after_chat_returns(monkeypatch):
    def fake_chat(*args, on_event, **kwargs):
        del args, kwargs
        on_event({"type": "delta", "delta": "streamed"})
        return {"status": "green", "response": "streamed"}

    monkeypatch.setattr(smi_chat_runtime, "chat", fake_chat)

    events = list(
        smi_chat_runtime.chat_events(
            "Review OAP.", "11111111-1111-4111-8111-111111111111", "OAP Member"
        )
    )

    assert [event["type"] for event in events] == ["delta", "complete"]
