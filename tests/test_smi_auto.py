from __future__ import annotations

import app as app_module
from mission_control import smi_auto
from smi_gateway import app as smi_gateway_app


def test_smi_auto_is_low_noise_and_never_executes():
    observed = smi_auto.observe("GET", "/the-spot/maps-weather-travel")

    assert observed["active"] is True
    assert observed["light"] == "purple"
    assert observed["provider_call_performed"] is False
    assert observed["database_write_performed"] is False
    assert observed["execution_granted"] is False
    assert observed["approval_granted"] is False
    assert observed["human_authority_final"] is True
    assert "truth" in observed["lenses"]
    assert "evidence" in observed["lenses"]
    assert "alignment" in observed["lenses"]


def test_smi_auto_escalates_writes_without_approving_them():
    observed = smi_auto.observe("POST", "/mission/judgement")

    assert observed["write_action"] is True
    assert observed["war_room_escalation"] is True
    assert "risk" in observed["lenses"]
    assert "decision" in observed["lenses"]
    assert "judgement" in observed["lenses"]
    assert observed["execution_granted"] is False
    assert observed["approval_granted"] is False


def test_oap_app_responses_expose_safe_smi_auto_headers(client):
    response = client.get("/the-spot")

    assert response.headers["X-OAP-SMI-Auto"] == "active"
    assert response.headers["X-OAP-SMI-Mode"] == "automatic_low_noise"
    assert response.headers["X-OAP-SMI-Execution"] == "blocked"


def test_smi_origin_enters_through_founder_sign_in_then_private_aliases():
    gateway = smi_gateway_app.test_client()

    assert gateway.get("/").headers["Location"] == "/auth?next=/mission/ollama"
    assert gateway.get("/smi").headers["Location"] == "/mission/ollama"
    assert gateway.get("/chat").headers["Location"] == "/mission/ollama"
    assert gateway.get("/war-room").headers["Location"] == "/mission/war-room"


def test_public_status_declares_same_non_authority_contract():
    snapshot = smi_auto.public_status()

    assert snapshot["active"] is True
    assert snapshot["mode"] == "automatic_low_noise"
    assert snapshot["provider_call_per_request"] is False
    assert snapshot["database_write_per_request"] is False
    assert snapshot["execution_granted"] is False
    assert snapshot["approval_granted"] is False
    assert snapshot["human_authority_final"] is True


def test_app_registers_smi_auto_response_hook():
    names = {func.__name__ for func in app_module.app.after_request_funcs[None]}
    assert "_oap_smi_auto_response" in names
