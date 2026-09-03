from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_gateway_is_oap_owned_and_local_first():
    text = (ROOT / "mission_control" / "oap_inference_gateway.py").read_text()
    assert "OAP Inference Gateway" in text
    assert "OAP_INFERENCE_LOCAL_URL" in text
    assert "OAP_INFERENCE_LOCAL_MODEL" in text
    assert "oap-core:latest" in text
    assert '"local_first": True' in text
    assert '"compatibility_fallback_present": True' in text
    assert "Human Authority" in text


def test_personal_smi_runtime_routes_through_gateway_before_core_provider():
    text = (ROOT / "mission_control" / "smi_chat_runtime.py").read_text()
    assert "oap_inference_gateway" in text
    assert "_gateway_provider" in text
    assert "_grounded.grounded_provider" in text
    assert "_core._provider = _grounded_provider" in text


def test_gateway_does_not_claim_full_provider_removal():
    text = (ROOT / "mission_control" / "oap_inference_gateway.py").read_text()
    assert "Compatibility fallback" in text or "compatibility fallback" in text
    assert "can be removed once the Home Node is reachable/certified" in text
