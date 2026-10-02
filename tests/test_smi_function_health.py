from __future__ import annotations

from pathlib import Path

import app as app_module
from mission_control import smi_function_health


def test_primary_founder_smi_routes_are_registered_and_deduplicated():
    payload = smi_function_health.route_status(app_module.app.url_map)

    assert payload["all_registered"] is True
    assert payload["registered_count"] == payload["expected_count"] == 13
    assert payload["availability_percent"] == 100.0
    assert payload["duplicate_primary_paths"] == 0
    assert payload["compatibility_aliases_hidden_from_primary_ui"] is True
    assert payload["public_private_separation"] is True
    assert payload["secrets_exposed"] is False
    assert payload["human_authority_final"] is True

    routes = {item["id"]: item for item in payload["routes"]}
    assert set(routes) == {
        "chat",
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


def test_function_health_covers_all_major_functions_without_fake_green(client, monkeypatch):
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
        smi_function_health.brain,
        "get_public_brain_status",
        lambda: {"validation": {"passed": True}, "brain_count": 1},
    )
    monkeypatch.setattr(
        smi_function_health.agents,
        "validate_agent_registry",
        lambda: {"passed": True, "registry_complete": True},
    )
    monkeypatch.setattr(
        smi_function_health.infrastructure,
        "get_public_infrastructure",
        lambda: {"validation": {"passed": True}},
    )
    monkeypatch.setattr(
        smi_function_health.judgement,
        "status",
        lambda: {"schema_ready": True, "ready": False, "error": None},
    )
    monkeypatch.setattr(
        smi_function_health.smi_recursive_improvement,
        "run_cycle",
        lambda: {
            "light": "orange",
            "proof": {"live_cycle_ran": True},
            "consequential_action": False,
        },
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

    assert payload["available_count"] == payload["expected_count"] == 13
    assert payload["availability_percent"] == 100.0
    assert payload["proof_checked_count"] == payload["expected_count"] == 13
    assert payload["proof_coverage_percent"] == 100.0
    assert payload["all_proof_sources_checked"] is True
    assert payload["runtime_ready_count"] == 12
    assert payload["runtime_ready_percent"] == 92.3
    assert payload["proof_required_count"] == 1
    assert payload["duplicate_primary_paths"] == 0
    assert payload["all_primary_routes_registered"] is True
    assert payload["whole_smi_green"] is False
    assert payload["execution_granted"] is False
    assert payload["no_fake_green"] is True
    assert payload["human_authority_final"] is True

    functions = {item["id"]: item for item in payload["functions"]}
    assert set(functions) == {
        "chat",
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
    for function_id in set(functions) - {"green-gate"}:
        assert functions[function_id]["proof_checked"] is True
        assert functions[function_id]["state"] == "green"
        assert functions[function_id]["label"] == "PROVEN"
    assert functions["green-gate"]["proof_checked"] is True
    assert functions["green-gate"]["state"] == "yellow"
    assert functions["green-gate"]["label"] == "PROOF REQUIRED"
    assert all(item["consequential_execution"] is False for item in functions.values())


def test_function_health_marks_missing_evidence_without_crashing(client, monkeypatch):
    def unavailable():
        raise RuntimeError("unavailable")

    monkeypatch.setattr(smi_function_health.brain, "get_public_brain_status", unavailable)

    response = client.get("/mission/smi/function-health")
    assert response.status_code == 200
    payload = response.get_json()
    functions = {item["id"]: item for item in payload["functions"]}

    assert functions["brain"]["proof_checked"] is False
    assert functions["brain"]["runtime_proven"] is False
    assert functions["brain"]["state"] == "yellow"
    assert functions["brain"]["label"] == "EVIDENCE UNAVAILABLE"
    assert payload["whole_smi_green"] is False
    assert payload["no_fake_green"] is True


def test_function_health_routes_fail_closed_anonymously(anonymous_client):
    for path in (
        "/mission/smi/function-health",
        "/mission/smi/routes",
        "/mission/smi/green-gate",
    ):
        response = anonymous_client.get(path)
        assert response.status_code == 401
        assert response.get_json()["error"]["code"] == "authentication_required"


def test_sovereign_dashboard_wires_core_routes_without_noise_duplicates():
    wrapper = Path("mission_control/templates/ollama_chat.html").read_text(encoding="utf-8")
    script = Path("mission_control/static/smi_sovereign_dashboard.js").read_text(encoding="utf-8")

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
        "Core Functions",
        "Function Health",
        "Green Gate",
        "21 Signals",
        "Guardian",
        "HRM",
        "cfg.functionHealthUrl",
        "cfg.greenGateUrl",
        "cfg.signalsUrl",
        "No duplicate controls",
    ):
        assert marker in script

    for noise in (
        "Mission Control','Founder command deck",
        "ISAC','Spatial intelligence proof",
        "Alignment','Provider and system alignment",
        "OAP World','Public front door",
        "Founder Recovery','Independent emergency access",
    ):
        assert noise not in script

    assert "silently deploy, spend, dispatch, migrate or approve consequential actions" in script


def test_interaction_certification_unlocks_only_control_surface_from_durable_receipt(monkeypatch):
    monkeypatch.setattr(
        smi_function_health.smi_receipt_backend,
        "latest_durable_button_proof",
        lambda: {
            "proven": True,
            "reason": "durable_post_ack_button_proof",
            "receipt_id": "receipt-live-control",
            "durable": True,
            "runtime_acknowledged": True,
            "click_only_proof": False,
            "status_code": 200,
        },
    )
    result = smi_function_health.interaction_certification()
    surfaces = {item["id"]: item for item in result["surfaces"]}

    assert result["implemented_count"] == result["expected_count"] == 9
    assert result["implementation_percent"] == 100.0
    assert result["live_proven_count"] == 1
    assert result["live_proof_percent"] == 11.1
    assert result["whole_interaction_green"] is False
    assert surfaces["control-surface-v2"]["live_runtime_proven"] is True
    assert surfaces["control-surface-v2"]["state"] == "green"
    assert surfaces["control-surface-v2"]["label"] == "LIVE PROVEN"
    assert surfaces["control-surface-v2"]["live_proof_receipt_id"] == "receipt-live-control"
    assert all(
        item["live_runtime_proven"] is False
        for item in result["surfaces"]
        if item["id"] != "control-surface-v2"
    )


def test_interaction_certification_fails_closed_without_durable_receipt(monkeypatch):
    monkeypatch.setattr(
        smi_function_health.smi_receipt_backend,
        "latest_durable_button_proof",
        lambda: {
            "proven": False,
            "reason": "durable_button_proof_missing",
            "receipt_id": None,
        },
    )
    result = smi_function_health.interaction_certification()
    assert result["live_proven_count"] == 0
    assert result["live_proof_percent"] == 0.0
    assert result["whole_interaction_green"] is False
    assert all(item["live_runtime_proven"] is False for item in result["surfaces"])


def test_interaction_certification_proves_chat_only_from_founder_interaction_gate(monkeypatch):
    monkeypatch.setattr(
        smi_function_health.smi_receipt_backend,
        "latest_durable_button_proof",
        lambda: {"proven": False, "reason": "missing", "receipt_id": None},
    )
    monkeypatch.setattr(
        smi_function_health.smi_completion_contract,
        "completion_status",
        lambda: {
            "proof_gates": (
                {"id": "founder_chat_interaction", "proven": True},
            )
        },
    )
    result = smi_function_health.interaction_certification()
    surfaces = {item["id"]: item for item in result["surfaces"]}

    assert result["live_proven_count"] == 1
    assert result["live_proof_percent"] == 11.1
    assert result["whole_interaction_green"] is False
    assert surfaces["chat"]["live_runtime_proven"] is True
    assert surfaces["chat"]["state"] == "green"
    assert surfaces["chat"]["label"] == "LIVE PROVEN"
    assert surfaces["chat"]["live_proof_source"] == "founder_chat_interaction_gate"
    assert surfaces["chat"]["live_proof_receipt_id"] is None
    assert all(
        item["live_runtime_proven"] is False
        for item in result["surfaces"]
        if item["id"] != "chat"
    )


def test_interaction_certification_combines_chat_and_control_without_overclaim(monkeypatch):
    monkeypatch.setattr(
        smi_function_health.smi_receipt_backend,
        "latest_durable_button_proof",
        lambda: {
            "proven": True,
            "receipt_id": "receipt-live-control",
            "runtime_acknowledged": True,
            "click_only_proof": False,
            "status_code": 200,
        },
    )
    monkeypatch.setattr(
        smi_function_health.smi_completion_contract,
        "completion_status",
        lambda: {
            "proof_gates": (
                {"id": "founder_chat_interaction", "proven": True},
            )
        },
    )
    result = smi_function_health.interaction_certification()
    surfaces = {item["id"]: item for item in result["surfaces"]}

    assert result["live_proven_count"] == 2
    assert result["live_proof_percent"] == 22.2
    assert result["whole_interaction_green"] is False
    assert surfaces["chat"]["live_runtime_proven"] is True
    assert surfaces["control-surface-v2"]["live_runtime_proven"] is True
    assert sum(item["live_runtime_proven"] for item in result["surfaces"]) == 2

def test_interaction_certification_consumes_independent_surface_proofs_without_overclaim(monkeypatch):
    monkeypatch.setattr(
        smi_function_health.smi_receipt_backend,
        "latest_durable_button_proof",
        lambda: {"proven": False, "reason": "missing", "receipt_id": None},
    )
    monkeypatch.setattr(
        smi_function_health.smi_completion_contract,
        "completion_status",
        lambda: {"proof_gates": ()},
    )
    monkeypatch.setattr(
        smi_function_health.smi_receipt_backend,
        "latest_durable_interaction_surface_proofs",
        lambda: {
            "voice": {
                "proven": True,
                "receipt_id": "receipt-live-voice",
                "source": "durable_interaction_surface_proof",
            },
            "vision": {
                "proven": True,
                "receipt_id": "receipt-live-vision",
                "source": "durable_interaction_surface_proof",
            },
        },
    )

    result = smi_function_health.interaction_certification()
    surfaces = {item["id"]: item for item in result["surfaces"]}

    assert result["live_proven_count"] == 2
    assert result["live_proof_percent"] == 22.2
    assert result["whole_interaction_green"] is False
    assert surfaces["voice"]["live_runtime_proven"] is True
    assert surfaces["voice"]["live_proof_receipt_id"] == "receipt-live-voice"
    assert surfaces["voice"]["live_proof_source"] == "durable_interaction_surface_proof"
    assert surfaces["vision"]["live_runtime_proven"] is True
    assert surfaces["vision"]["live_proof_receipt_id"] == "receipt-live-vision"
    assert all(
        item["live_runtime_proven"] is False
        for item in result["surfaces"]
        if item["id"] not in {"voice", "vision"}
    )


def test_interaction_certification_fails_closed_when_surface_proof_reader_errors(monkeypatch):
    monkeypatch.setattr(
        smi_function_health.smi_receipt_backend,
        "latest_durable_button_proof",
        lambda: {"proven": False, "reason": "missing", "receipt_id": None},
    )
    monkeypatch.setattr(
        smi_function_health.smi_completion_contract,
        "completion_status",
        lambda: {"proof_gates": ()},
    )

    def _boom():
        raise RuntimeError("proof store unavailable")

    monkeypatch.setattr(
        smi_function_health.smi_receipt_backend,
        "latest_durable_interaction_surface_proofs",
        _boom,
    )

    result = smi_function_health.interaction_certification()
    assert result["live_proven_count"] == 0
    assert result["live_proof_percent"] == 0.0
    assert result["whole_interaction_green"] is False
    assert all(item["live_runtime_proven"] is False for item in result["surfaces"])

