from __future__ import annotations

from mission_control import smi_command_dashboard


def test_smi_command_dashboard_composes_canonical_sources():
    command = smi_command_dashboard.status()

    assert command["component"] == "SMI Founder Command Dashboard"
    assert command["brain"]["count"] == 1
    assert command["brain"]["regions"] == 14
    assert command["brain"]["lenses"] == 26
    assert command["intelligence"]["worlds"] == 7
    assert command["intelligence"]["agents"] == 78
    assert command["bank"]["software_controls_present"] is True
    assert command["bank"]["account_engine_present"] is True
    assert command["bank"]["single_pay_gateway"] is True
    assert command["bank"]["rights_record_required"] is True
    assert command["bank"]["orchestrator_present"] is True
    assert command["bank"]["direct_authorisation_bypass_allowed"] is False
    assert command["bank"]["regulated_execution_enabled"] is False
    assert command["bank"]["operational_bank"] is False
    assert command["bank"]["licence_verified"] is False
    assert command["bank"]["money_movement"] is False
    assert command["risk_router"]["routes"] == (
        "DIRECT_ANSWER",
        "PREPARE",
        "CONFIRM",
        "GOVERNANCE",
        "BLOCK",
    )
    assert command["execution_granted"] is False
    assert command["approval_granted"] is False
    assert command["human_authority_final"] is True


def test_smi_command_dashboard_route_is_read_only(client):
    response = client.get("/mission/smi")
    page = response.get_data(as_text=True)

    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    assert "SMI Command Dashboard" in page
    assert "All Intelligence" in page
    assert "War Room" in page
    assert "Bank / SIKA" in page
    assert "direct bypass closed" in page
    assert "regulated execution locked" in page
    assert "DIRECT_ANSWER" in page
    assert 'method="post"' not in page.lower()
    assert client.post("/mission/smi").status_code == 405


def test_smi_command_dashboard_status_is_redacted_read_only(client):
    response = client.get("/mission/smi/status")
    payload = response.get_json()
    serialized = response.get_data(as_text=True).lower()

    assert response.status_code == 200
    assert payload["execution_granted"] is False
    assert payload["approval_granted"] is False
    assert payload["human_authority_final"] is True
    assert payload["bank"]["software_controls_present"] is True
    assert payload["bank"]["single_pay_gateway"] is True
    assert payload["bank"]["direct_authorisation_bypass_allowed"] is False
    assert payload["bank"]["regulated_execution_enabled"] is False
    assert payload["bank"]["money_movement"] is False
    for forbidden in ("password", "private_key", "signing_key", "secret", "token"):
        assert forbidden not in serialized
