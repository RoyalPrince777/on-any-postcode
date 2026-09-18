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


def test_button_proof_separates_server_runtime_from_browser_click(monkeypatch):
    monkeypatch.setattr(
        smi_function_health,
        "function_health",
        lambda _url_map: {
            "functions": (
                {
                    "id": "chat",
                    "name": "SMI Chat",
                    "path": "/mission/ollama",
                    "available": True,
                    "proof_checked": True,
                    "runtime_proven": True,
                },
                {
                    "id": "green-gate",
                    "name": "Green Gate",
                    "path": "/mission/smi/green-gate",
                    "available": True,
                    "proof_checked": True,
                    "runtime_proven": False,
                },
            )
        },
    )
    payload = smi_function_health.button_proof(app_module.app.url_map)
    assert payload["expected_count"] == 2
    assert payload["server_ready_count"] == 1
    assert payload["browser_click_ready_count"] == 0
    assert payload["whole_button_gate_green"] is False

    clicked = smi_function_health.button_proof(
        app_module.app.url_map,
        clicked_ids=("chat",),
    )
    assert clicked["browser_click_ready_count"] == 1
    assert clicked["buttons"][0]["browser_click_proven"] is True
    assert payload["no_fake_green"] is True


def test_button_proof_route_is_founder_only(client):
    response = client.get("/mission/smi/button-proof")
    assert response.status_code == 200
    assert response.get_json()["component"] == "SMI Founder Button Proof"


def test_button_proof_route_rejects_anonymous_access(anonymous_client):
    response = anonymous_client.get("/mission/smi/button-proof")
    assert response.status_code == 401
    assert response.get_json()["error"]["code"] == "authentication_required"


def test_button_click_receipt_route_requires_csrf_and_known_success(client, monkeypatch):
    monkeypatch.setattr(
        smi_function_health,
        "FUNCTION_SPECS",
        ({"id": "chat", "name": "SMI Chat", "endpoint": "mission_control.ollama_chat_dashboard", "path": "/mission/ollama"},),
    )
    no_csrf = client.post(
        "/mission/smi/button-proof/click",
        json={"button_id": "chat", "response_class": "success"},
    )
    assert no_csrf.status_code == 403

    with client.session_transaction() as session:
        csrf = session.get("oap_csrf_token")
    if not csrf:
        client.get("/mission/ollama")
        with client.session_transaction() as session:
            csrf = session.get("oap_csrf_token")

    unknown = client.post(
        "/mission/smi/button-proof/click",
        headers={"X-OAP-CSRF": csrf},
        json={"button_id": "unknown", "response_class": "success"},
    )
    assert unknown.status_code == 400

    failed = client.post(
        "/mission/smi/button-proof/click",
        headers={"X-OAP-CSRF": csrf},
        json={"button_id": "chat", "response_class": "failed"},
    )
    assert failed.status_code == 400


def test_button_proof_reads_successful_click_receipts(client, monkeypatch):
    from mission_control import alignment_views

    monkeypatch.setattr(
        alignment_views.smi_receipt_backend,
        "latest_safe_payloads",
        lambda kind, limit=200: (
            {"button_id": "chat", "response_class": "success"},
        ),
    )
    monkeypatch.setattr(
        smi_function_health,
        "function_health",
        lambda _url_map: {
            "functions": (
                {
                    "id": "chat",
                    "name": "SMI Chat",
                    "path": "/mission/ollama",
                    "available": True,
                    "proof_checked": True,
                    "runtime_proven": True,
                },
            )
        },
    )
    response = client.get("/mission/smi/button-proof")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["server_ready_count"] == 1
    assert payload["browser_click_ready_count"] == 1
    assert payload["whole_button_gate_green"] is True
