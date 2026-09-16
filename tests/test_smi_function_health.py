from __future__ import annotations

from pathlib import Path

import app as app_module
from mission_control import smi_function_health


def test_primary_founder_smi_routes_are_registered():
    payload = smi_function_health.route_status(app_module.app.url_map)

    assert payload["all_registered"] is True
    assert payload["registered_count"] == payload["expected_count"] == 14
    assert payload["public_private_separation"] is True
    assert payload["secrets_exposed"] is False
    assert payload["human_authority_final"] is True

    routes = {item["id"]: item for item in payload["routes"]}
    assert set(routes) == {
        "chat",
        "live-monitor",
        "signals-21",
        "war-room",
        "guardian",
        "hrm",
        "brain",
        "agents",
        "infrastructure",
        "judgement",
        "improvement",
        "function-health",
        "routes",
        "green-gate",
    }
    assert routes["guardian"]["path"].endswith("command=guardian_check")
    assert routes["function-health"]["path"] == "/mission/smi/function-health"
    assert routes["routes"]["path"] == "/mission/smi/routes"
    assert routes["green-gate"]["path"] == "/mission/smi/green-gate"
    assert all(item["external_execution"] is False for item in routes.values())


def test_function_health_is_truth_labelled_and_never_grants_execution(
    client, monkeypatch
):
    monkeypatch.setattr(
        smi_function_health.smi_chat_runtime,
        "health",
        lambda: {
            "status": "green",
            "checks": {
                "chat_route": True,
                "war_room": True,
                "conversation_memory": True,
            },
        },
    )
    monkeypatch.setattr(
        smi_function_health.coherent_automation,
        "status",
        lambda: {"ready": True, "signals_valid": True, "signal_count": 21},
    )
    monkeypatch.setattr(
        smi_function_health.smi_proof_gate,
        "public_safe_status",
        lambda: {
            "component": "SMI Green Gate",
            "green": False,
            "light": "🟡",
            "checks": {"observability": False},
            "missing": ("observability",),
            "execution_granted": False,
            "human_authority_final": True,
        },
    )

    response = client.get("/mission/smi/function-health")
    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    payload = response.get_json()

    assert payload["available_count"] == payload["expected_count"] == 14
    assert payload["all_primary_routes_registered"] is True
    assert payload["whole_smi_green"] is False
    assert payload["execution_granted"] is False
    assert payload["no_fake_green"] is True
    assert payload["human_authority_final"] is True

    functions = {item["id"]: item for item in payload["functions"]}
    assert functions["chat"]["state"] == "green"
    assert functions["war-room"]["state"] == "green"
    assert functions["hrm"]["state"] == "green"
    assert functions["signals-21"]["state"] == "green"
    assert functions["guardian"]["state"] == "green"
    assert functions["green-gate"]["state"] == "yellow"
    assert functions["green-gate"]["label"] == "PROOF REQUIRED"
    assert all(item["consequential_execution"] is False for item in functions.values())


def test_function_health_routes_fail_closed_anonymously(anonymous_client):
    for path in (
        "/mission/smi/function-health",
        "/mission/smi/routes",
        "/mission/smi/green-gate",
    ):
        response = anonymous_client.get(path)
        assert response.status_code == 401
        assert response.get_json()["error"]["code"] == "authentication_required"


def test_sovereign_dashboard_wires_real_function_routes():
    wrapper = Path("mission_control/templates/ollama_chat.html").read_text(
        encoding="utf-8"
    )
    script = Path("mission_control/static/smi_sovereign_dashboard.js").read_text(
        encoding="utf-8"
    )

    for marker in (
        "functionHealthUrl",
        "routesUrl",
        "greenGateUrl",
        "signalsUrl",
        "guardianUrl",
        "hrmUrl",
        "alignment.smi_function_health_status",
        "alignment.smi_route_status",
        "alignment.green_gate_status",
    ):
        assert marker in wrapper

    for marker in (
        "Function Health",
        "Green Gate",
        "21 Signals",
        "Guardian",
        "HRM",
        "cfg.functionHealthUrl",
        "cfg.greenGateUrl",
        "cfg.signalsUrl",
    ):
        assert marker in script

    assert "whole_smi_green" not in script
    assert "silently execute consequential actions" in script
