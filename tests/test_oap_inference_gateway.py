from pathlib import Path

from mission_control import oap_inference_gateway
from oap.smi.capability_fabric import select_capabilities
from oap.smi.capability_fabric import status as capability_status

ROOT = Path(__file__).resolve().parents[1]


def test_gateway_is_oap_owned_and_local_first():
    text = (ROOT / "mission_control" / "oap_inference_gateway.py").read_text()
    assert "OAP Inference Gateway" in text
    assert "OAP_INFERENCE_LOCAL_URL" in text
    assert "OAP_INFERENCE_LOCAL_MODEL" in text
    assert "oap-core:latest" in text
    assert '"local_first": True' in text
    assert '"compatibility_fallback_enabled": FALLBACK_ENABLED' in text
    assert '"first_party_inference_ready": first_party_ready' in text
    assert "Human Authority" in text


def test_personal_smi_runtime_routes_through_gateway_before_core_provider():
    text = (ROOT / "mission_control" / "smi_chat_runtime.py").read_text()
    assert "oap_inference_gateway" in text
    assert "_gateway_provider" in text
    assert "_grounded.grounded_provider" in text
    assert "_core._provider = _grounded_provider" in text


def test_gateway_does_not_claim_full_provider_removal():
    text = (ROOT / "mission_control" / "oap_inference_gateway.py").read_text()
    assert "compatibility engine only while first-party inference is not certified" in text
    assert "if not FALLBACK_ENABLED" in text
    assert 'raise RuntimeError("first_party_inference_required")' in text
    assert '"sovereign_inference_ready": bool(first_party_ready and not FALLBACK_ENABLED)' in text


def test_capability_fabric_combines_functions_without_provider_identity_or_authority():
    snapshot = capability_status()
    assert snapshot["ready"] is True
    assert snapshot["capability_count"] >= 15
    assert snapshot["provider_neutral"] is True
    assert snapshot["copies_provider_identity"] is False
    assert snapshot["copies_private_prompts"] is False
    assert snapshot["copies_model_weights"] is False
    assert snapshot["external_provider_authority"] is False
    capabilities = select_capabilities(
        "TECHNICAL",
        "Research the latest sources, review this complex code and compare approaches",
        high_impact=True,
    )
    assert "adaptive_reasoning" in capabilities
    assert "agentic_code_review" in capabilities
    assert "advisor_challenger" in capabilities
    assert "cited_live_research" in capabilities
    assert "evidence_first" in capabilities


def test_gateway_enriches_all_provider_paths_with_oap_capabilities():
    enriched = oap_inference_gateway._enrich_brain(
        "Review and fix this code with tests and evidence",
        {"task_type": "TECHNICAL", "high_impact": True},
    )
    assert "agentic_code_review" in enriched["intelligence_capabilities"]
    assert "evidence_first" in enriched["intelligence_capabilities"]
    assert enriched["external_provider_authority"] is False
    assert enriched["human_authority_final"] is True
    assert oap_inference_gateway.status()["capability_fabric"]["ready"] is True
