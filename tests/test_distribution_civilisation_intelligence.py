from __future__ import annotations

from mission_control import distribution_intelligence
from oap.smi.agi_core import AGICore


def test_distribution_contract_is_nested_inside_civilisation_intelligence():
    status = distribution_intelligence.status()

    assert status["canonical_world_id"] == "civilisation"
    assert status["canonical_world_name"] == "Civilisation Intelligence"
    assert status["kind"] == "specialist_intelligence_capability"
    assert status["creates_new_world"] is False
    assert status["creates_agent_family"] is False
    assert status["publishing_authority_granted"] is False
    assert status["payment_authority_granted"] is False
    assert status["external_execution_enabled"] is False
    assert status["human_authority_final"] is True


def test_distribution_terms_route_to_civilisation_without_eighth_world():
    core = AGICore()
    route = core.route(
        "Prepare creator distribution, publishing rights proof and a music release campaign.",
        "CULTURE",
    )
    status = core.status()

    assert status["world_count"] == 7
    assert status["canonical_world_model"] is True
    assert "distribution" in route["specialist_ids"]
    assert "Distribution Intelligence" in route["specialists"]
    assert "civilisation" in route["world_ids"]
    assert "Civilisation Intelligence" in route["worlds"]
    assert route["world_count_limit"] == 7
    assert route["decision_authority"] is False
    assert route["execution_authority"] is False


def test_distribution_release_review_preserves_authority_boundary():
    result = distribution_intelligence.review_release(
        {
            "title": "OAP release",
            "rights_proof": True,
            "campaign_ready": True,
            "human_approval": True,
            "external_adapter_proven": False,
            "receipt_destination": True,
        }
    )

    assert result["canonical_world_id"] == "civilisation"
    assert result["capability_kind"] == "specialist_intelligence_capability"
    assert result["owned_oap_distribution_ready"] is True
    assert result["external_distribution_ready"] is False
    assert result["execution_performed"] is False
    assert result["publishing_authority_granted"] is False
    assert result["payment_authority_granted"] is False
    assert result["human_authority_final"] is True
