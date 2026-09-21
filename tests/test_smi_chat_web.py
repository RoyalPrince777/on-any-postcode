from __future__ import annotations

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


def test_direct_core_provider_alias_is_fail_closed_even_with_external_key(monkeypatch):
    import pytest

    from mission_control import smi_chat_runtime_core

    def forbidden_network(*args, **kwargs):
        raise AssertionError("external_provider_call")

    monkeypatch.setenv("OPENAI_API_KEY", "test-provider-key")
    monkeypatch.setattr(smi_chat_runtime.urlrequest, "urlopen", forbidden_network)
    with pytest.raises(RuntimeError, match="first_party_inference_required"):
        smi_chat_runtime._provider("Private Founder context")
    with pytest.raises(RuntimeError, match="first_party_inference_required"):
        smi_chat_runtime_core._provider("Private Founder context")
    with pytest.raises(RuntimeError, match="first_party_inference_required"):
        smi_chat_runtime._COMPATIBILITY_ENGINE("Private Founder context")


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


def test_completed_chat_records_step1_behaviour_receipt(monkeypatch):
    monkeypatch.setattr(
        smi_chat_runtime._core,
        "chat",
        lambda *args, **kwargs: {
            "status": "green",
            "request_id": "req-1",
            "conversation_id": "conv-1",
            "response": "Done",
            "output_state": "RECOMMENDATION_ONLY",
            "guardian": "PASSED",
        },
    )
    monkeypatch.setattr(
        smi_chat_runtime._intelligence,
        "public_route",
        lambda message: {"active": False, "mode": "none", "subject": ""},
    )
    monkeypatch.setattr(
        smi_chat_runtime._thinking,
        "completion_summary",
        lambda result: {"status": "complete"},
    )
    monkeypatch.setattr(
        smi_chat_runtime._thinking,
        "process_contract",
        lambda: {
            "name": "test",
            "version": 1,
            "stage_count": 5,
            "first_party_only": True,
            "private_reasoning_exposed": False,
            "chain_of_thought_exposed": False,
            "human_authority_final": True,
        },
    )
    monkeypatch.setattr(smi_chat_runtime, "canonical_memory_status", dict)
    monkeypatch.setattr(smi_chat_runtime, "governed_memory_status", dict)
    monkeypatch.setattr(smi_chat_runtime, "memory_sync_status", dict)
    captured = []

    def fake_receipt(kind, payload):
        captured.append({"kind": kind, "payload": payload})
        return {
            "ok": True,
            "receipt_id": (
                "behaviour-score-r2"
                if kind == "behaviour_score_receipt"
                else "behaviour-r1"
            ),
            "receipt_kind": kind,
            "durable": True,
        }

    monkeypatch.setattr(smi_chat_runtime._receipts, "write_receipt", fake_receipt)

    result = smi_chat_runtime.chat(
        "Review OAP.",
        "11111111-1111-4111-8111-111111111111",
        "OAP Member",
        thinking_level="think",
    )

    assert [item["kind"] for item in captured] == [
        "behaviour_response_receipt",
        "behaviour_score_receipt",
        "behaviour_learning_receipt",
        "behaviour_step4_readiness_receipt",
    ]
    step1 = captured[0]["payload"]
    assert step1["gate"] == 1
    safe = step1["safe_payload"]
    assert safe["protocol_percentage"] == 25
    assert safe["scores_calculated"] is False
    assert safe["behaviour_learning_applied"] is False
    assert safe["war_room_escalation_applied"] is False
    assert len(safe["dimension_ids"]) == 21
    assert result["behaviour_receipt"] == {
        "ok": True,
        "receipt_id": "behaviour-r1",
        "receipt_kind": "behaviour_response_receipt",
        "durable": True,
        "protocol_step": 1,
        "protocol_percentage": 25,
        "scores_calculated": False,
    }

    step2 = captured[1]["payload"]
    assert step2["gate"] == 2
    scored = step2["safe_payload"]
    assert scored["protocol_percentage"] == 50
    assert scored["measured_count"] == 9
    assert scored["unknown_count"] == 12
    assert scored["coverage_percentage"] == 43
    assert scored["measured_average_percentage"] == 67
    assert scored["overall_percentage"] is None
    assert scored["overall_evidence_state"] == "partial"
    assert scored["behaviour_learning_applied"] is False
    assert scored["war_room_escalation_applied"] is False
    assert scored["full_green_allowed"] is False
    assert result["behaviour_score_receipt"]["receipt_id"] == "behaviour-score-r2"
    assert result["behaviour_score_receipt"]["protocol_percentage"] == 50
    assert result["behaviour_score_receipt"]["overall_percentage"] is None
    assert result["behaviour_score_receipt"]["full_green_allowed"] is False
    assert result["behaviour_learning_receipt"]["protocol_percentage"] == 75
    assert result["behaviour_learning_receipt"]["self_apply_changes"] is False
    assert result["behaviour_step4_receipt"]["protocol_percentage"] == 100
    assert result["behaviour_step4_receipt"]["step4_readiness_only"] is True
    assert result["behaviour_step4_receipt"]["green_gate_passed"] is False
    assert result["behaviour_step4_receipt"]["founder_final"] == "waiting"
    assert result["behaviour_step4_receipt"]["full_green"] is False


def test_text_chat_does_not_require_compatibility_provider_key_before_first_party_route():
    from pathlib import Path

    code = (Path(__file__).parents[1] / "mission_control" / "smi_chat_runtime_core.py").read_text()
    assert 'if attachment and not provider_key:' in code
    assert 'raise RuntimeError("provider_key_missing_for_media")' in code
    assert 'if not provider_key:\n            raise RuntimeError("provider_key_missing")' not in code


def test_count_integrity_budget_supports_requested_seven_items():
    from pathlib import Path

    core = (
        Path(__file__).parents[1] / "mission_control" / "smi_chat_runtime_core.py"
    ).read_text()
    gateway = (
        Path(__file__).parents[1] / "mission_control" / "oap_inference_gateway.py"
    ).read_text()
    assert "COUNT INTEGRITY" in core
    assert "requested_count * 230" in core
    assert '"num_predict": num_predict' in gateway
