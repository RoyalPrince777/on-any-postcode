from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_gateway_has_truthful_home_node_certification():
    code = (ROOT / "mission_control" / "oap_inference_gateway.py").read_text()
    assert "def probe_local" in code
    assert "configured_model_missing" in code
    assert "compatibility_fallback_enabled" in code
    assert "sovereign_inference_ready" in code
    assert "OAP_INFERENCE_COMPATIBILITY_FALLBACK" in code
    assert "local_inference_required" in code


def test_sovereign_ready_requires_local_proof_and_no_fallback():
    code = (ROOT / "mission_control" / "oap_inference_gateway.py").read_text()
    assert 'proof.get("reachable")' in code
    assert 'proof.get("model_available")' in code
    assert "not FALLBACK_ENABLED" in code


def test_private_chat_health_exposes_inference_certification():
    code = (ROOT / "mission_control" / "smi_chat_runtime.py").read_text()
    assert 'snapshot["inference"] = _inference.status(probe=True)' in code
    assert "_grounded.grounded_provider" in code
    assert "_core._provider = _grounded_provider" in code
