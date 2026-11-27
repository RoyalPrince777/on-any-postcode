from mission_control import oap_inference_gateway as gateway


def test_native_probe_opt_in_and_never_falls_back(monkeypatch):
    availability = {"reachable": True, "model_available": True}
    monkeypatch.delenv("OAP_SMI_NATIVE_INFERENCE_PROBE", raising=False)
    assert gateway.probe_native_inference(availability)["attempted"] is False
    monkeypatch.setenv("OAP_SMI_NATIVE_INFERENCE_PROBE", "1")
    monkeypatch.setattr(gateway, "LOCAL_ENABLED", True)
    monkeypatch.setattr(gateway, "LOCAL_URL", "http://127.0.0.1:11434/api/chat")
    monkeypatch.setattr(gateway, "LOCAL_MODEL", "oap-core:latest")
    seen = []

    def response(req, *, timeout):
        seen.append((req.full_url, timeout))
        return {
            "model": "oap-core:latest", "done": True,
            "message": {"content": "READY"}, "eval_count": 1,
        }

    monkeypatch.setattr(gateway, "_read_local_json", response)
    state = gateway.probe_native_inference(availability)
    assert seen == [("http://127.0.0.1:11434/api/chat", 5.0)]
    assert state["local_response_observed"] is True
    assert state["model_identity_independently_verified"] is False
    assert state["engineering_execution_verified"] is False
    assert state["external_fallback_used"] is False
    assert len(state["response_sha256"]) == 64
    assert "content" not in state
    monkeypatch.setattr(gateway, "_read_local_json", lambda *_args, **_kw: {"done": True})
    assert not gateway.probe_native_inference(availability)["local_response_observed"]
    monkeypatch.setattr(gateway, "LOCAL_URL", "http://example.com/api/chat")
    assert not gateway.probe_native_inference(availability)["attempted"]
