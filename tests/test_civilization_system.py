from __future__ import annotations

from mission_control import civilization


def test_living_digital_civilization_registry_is_coherent():
    result = civilization.validate_civilization_system()
    assert result["passed"] is True
    assert result["errors"] == []
    assert result["checks"]["one_brain"] is True
    assert result["checks"]["human_authority_final"] is True
    assert result["checks"]["no_fake_green"] is True


def test_civilization_status_keeps_architecture_separate_from_live_green():
    status = civilization.get_civilization_status()
    assert status["name"] == "OAP Living Digital Civilization System"
    assert status["status"] == "architecture_protocol_defined"
    assert status["operational_green"] is False
    assert status["governance"]["proof_before_green"] is True
    assert status["governance"]["human_approval_before_consequential_action"] is True


def test_protocol_and_supplier_boundary_are_locked():
    assert civilization.LIVING_LOOP == (
        "SENSE",
        "VERIFY",
        "UNDERSTAND",
        "COORDINATE",
        "AUTHORIZE",
        "ACT",
        "OBSERVE",
        "LEARN",
        "RECOVER",
    )
    assert tuple(g["percent"] for g in civilization.PROTOCOL_GATES) == (
        "25",
        "50",
        "75",
        "100",
    )
    assert "canonical_identity" in civilization.FIRST_PARTY_AUTHORITY
    assert "compute_hosting" in civilization.REPLACEABLE_SUPPLIERS


def test_civilization_route_is_private_and_truth_labelled(client):
    response = client.get("/mission/civilization")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["operational_green"] is False
    assert payload["validation"]["passed"] is True
