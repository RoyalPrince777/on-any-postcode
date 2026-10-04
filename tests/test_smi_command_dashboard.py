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
    unlock = command["bank"]["regulated_unlock"]
    assert unlock["total"] == 8
    assert unlock["unlocked_count"] >= 0
    assert set(unlock["capabilities"]) == {
        "accept_deposits",
        "bank_accounts",
        "cash_out",
        "execute_payments",
        "foreign_exchange",
        "hold_customer_funds",
        "issue_payment_cards",
        "issue_redeemable_sika",
    }
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
    assert "SMI Home" in page
    assert "Seven doors" in page
    assert "Phone" in page
    assert "Walkie-Talkie" in page
    assert "Messages" in page
    assert "My Line / eSIM" in page
    assert "OAP Mail" in page
    assert "Outbound relay built" in page
    assert "Telecom truth review" in page
    assert "Graphs" in page
    assert "Monitors" in page
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



def test_regulated_unlock_matrix_fails_closed_when_evidence_store_unavailable(monkeypatch):
    monkeypatch.setattr(
        smi_command_dashboard.sika_execution_gate,
        "capability_matrix",
        lambda: (_ for _ in ()).throw(
            smi_command_dashboard.bank_authorisation_store.BankEvidenceUnavailable(
                "store unavailable"
            )
        ),
    )
    unlock = smi_command_dashboard._regulated_unlock_matrix()
    assert unlock["evidence_available"] is False
    assert unlock["unlocked_count"] == 0
    assert unlock["all_unlocked"] is False
    assert all(value is False for value in unlock["capabilities"].values())


def test_smi_home_has_exactly_seven_unique_doors_and_truthful_mail_scope():
    command = smi_command_dashboard.status()
    doors = command["doors"]
    assert len(doors) == 7
    assert len({door["id"] for door in doors}) == 7
    assert [door["id"] for door in doors] == [
        "smi", "command", "interaction", "control", "lab", "studio", "recovery"
    ]
    assert command["interaction"]["phone"]["built"] is True
    assert command["interaction"]["walkie_talkie"]["built"] is True
    assert command["interaction"]["messages"]["built"] is True
    assert command["interaction"]["my_line"]["built"] is True
    assert command["interaction"]["oap_mail"]["built"] is True
    assert command["interaction"]["oap_mail"]["href"] == "/mail/status"
    assert command["interaction"]["oap_mail"]["inbox_receive_built"] is False
    assert command["interaction"]["incoming"]["href"] == "/linkup/incoming"
    assert command["interaction"]["recents"]["href"] == "/linkup/calls/recents"
    assert command["telecom"]["validation_passed"] is True
    assert command["telecom"]["software_control_plane_ready"] is True
    assert command["telecom"]["seven_stars"]["truth"] == "PROVEN"
    assert command["telecom"]["seven_stars"]["compliance"] in {"PROVEN", "BLOCKED"}


def test_smi_home_cockpit_is_low_noise_and_route_backed():
    command = smi_command_dashboard.status()
    assert [item["id"] for item in command["cockpit"]] == [
        "brain", "graphs", "monitors", "signals", "incoming", "nexus"
    ]
    assert command["interaction"]["phone"]["href"] == "/linkup?intent=link-call"
    assert command["interaction"]["walkie_talkie"]["href"] == "/linkup?intent=ptt"
    assert command["interaction"]["messages"]["href"] == "/linkup?intent=message"
    assert command["interaction"]["my_line"]["href"] == "/my-line"
