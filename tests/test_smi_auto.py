from __future__ import annotations

from mission_control import smi_auto
from smi_gateway import app as smi_gateway_app


def test_smi_auto_is_low_noise_and_never_grants_execution():
    state = smi_auto.observe("GET", "/the-spot")

    assert state["active"] is True
    assert state["mode"] == "automatic_low_noise"
    assert state["lenses"][:3] == ("truth", "evidence", "alignment")
    assert state["provider_call_performed"] is False
    assert state["database_write_performed"] is False
    assert state["execution_granted"] is False
    assert state["approval_granted"] is False
    assert state["human_authority_final"] is True


def test_smi_auto_selects_domain_lenses_and_escalates_consequential_writes():
    maps = smi_auto.observe("GET", "/atlas/api/local-map")
    assert {"dependency", "architecture", "risk", "performance"} <= set(maps["lenses"])
    assert maps["war_room_escalation"] is False

    booking_write = smi_auto.observe("POST", "/travel/direct/api/reservations")
    assert {"risk", "security", "privacy", "readiness", "decision", "judgement"} <= set(booking_write["lenses"])
    assert booking_write["war_room_escalation"] is True
    assert booking_write["execution_granted"] is False


def test_private_smi_routes_receive_security_and_privacy_lenses():
    state = smi_auto.observe("GET", "/mission/ollama", "mission_control.ollama_chat_dashboard")
    assert state["private_surface"] is True
    assert {"security", "privacy"} <= set(state["lenses"])


def test_oap_app_responses_expose_safe_smi_auto_headers(client):
    response = client.get("/the-spot")

    assert response.headers["X-OAP-SMI-Auto"] == "active"
    assert response.headers["X-OAP-SMI-Mode"] == "automatic_low_noise"
    assert response.headers["X-OAP-SMI-Execution"] == "blocked"


def test_smi_origin_opens_personal_smi_directly():
    gateway = smi_gateway_app.test_client()

    assert gateway.get("/").headers["Location"] == "/mission/ollama"
    assert gateway.get("/smi").headers["Location"] == "/mission/ollama"
    assert gateway.get("/chat").headers["Location"] == "/mission/ollama"
    assert gateway.get("/war-room").headers["Location"] == "/mission/war-room"
