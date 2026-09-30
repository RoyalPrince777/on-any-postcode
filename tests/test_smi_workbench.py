import json
from pathlib import Path

from mission_control import music_civilization_migration, smi_workbench, web_security


def test_workbench_projection_never_exposes_secret_values(monkeypatch):
    monkeypatch.setenv("OAP_GITHUB_TOKEN", "github-secret-value")
    monkeypatch.setenv("RENDER_API_KEY", "render-secret-value")
    monkeypatch.setenv("DATABASE_URL", "postgresql://secret@host/database")
    monkeypatch.setattr(
        smi_workbench.smi_chat_runtime,
        "health",
        lambda: {"status": "yellow", "checks": {"database": False, "schema": False}},
    )

    payload = smi_workbench.get_workbench_status()
    serialized = json.dumps(payload)
    connectors = {item["id"]: item for item in payload["connectors"]}
    capabilities = {item["id"]: item for item in payload["capabilities"] if "id" in item}

    assert list(connectors) == ["render", "github", "neon"]
    assert all(item["configured"] for item in connectors.values())
    assert connectors["render"]["inspect_url"] == "/mission/tools/render/services"
    assert connectors["github"]["inspect_url"] == "/mission/tools/github/repository"
    assert connectors["neon"]["inspect_url"] == "/mission/tools/neon/status"
    assert connectors["neon"]["name"] == "Neon · Identity/HRM blocked"
    assert connectors["render"]["ready"] is False
    assert connectors["render"]["configured"] is True
    assert connectors["render"]["provider_api_configured"] is True
    assert connectors["github"]["ready"] is True
    assert connectors["github"]["inspect_available"] is True
    assert connectors["github"]["access_mode"] == "authenticated-api"
    assert payload["runtime_gate"]["state"] == "yellow"
    assert payload["runtime_gate"]["fail_closed"] is True
    assert "managed Founder identity" in payload["runtime_gate"]["blocked"]
    assert "Founder read-only provider inspection" in payload["runtime_gate"]["available"]
    assert "secret-value" not in serialized
    assert "postgresql://" not in serialized
    assert payload["governance"]["human_authority_final"] is True
    assert payload["governance"]["provider_reads_founder_only"] is True
    assert payload["truth_contract"]["no_fake_green"] is True
    assert payload["truth_contract"]["green_requires_runtime_evidence"] is True
    assert capabilities["attachments"]["ready"] is False
    assert capabilities["voice"]["ready"] is False
    assert capabilities["code"]["ready"] is False


def test_workbench_runtime_gate_turns_green_only_with_database_and_schema(monkeypatch):
    monkeypatch.setattr(
        smi_workbench.smi_chat_runtime,
        "health",
        lambda: {
            "status": "green",
            "checks": {
                "database": True,
                "schema": True,
                "chat_route": True,
                "conversation_memory": True,
                "war_room": True,
            },
        },
    )

    payload = smi_workbench.get_workbench_status()
    neon = next(item for item in payload["connectors"] if item["id"] == "neon")

    assert payload["runtime_gate"]["state"] == "green"
    assert payload["runtime_gate"]["fail_closed"] is False
    assert payload["runtime_gate"]["blocked"] == []
    assert neon["name"] == "Neon · Identity/HRM"
    assert neon["ready"] is True
    assert payload["status"] == "ready"


def test_workbench_status_is_private(anonymous_client):
    response = anonymous_client.get("/mission/workbench/status")
    assert response.status_code == 401
    assert response.get_json()["error"]["code"] == "authentication_required"


def test_personal_smi_has_quiet_tools_workbench():
    page = Path("mission_control/templates/ollama_chat.html").read_text(encoding="utf-8")
    assert "Quiet 2027 workbench" in page
    assert "Open connected tools" in page
    assert "Credentials are never shown" in page
    assert "workbenchUrl" in page
    assert "inspect_url" in page
    assert "Inspect" in page
    assert "Reading governed provider state" in page


def test_music_release_evidence_link_is_private_and_inert(monkeypatch):
    def unexpected_inventory():
        raise AssertionError("Workbench status must not inspect the database")

    monkeypatch.setattr(
        music_civilization_migration, "inspect", unexpected_inventory
    )
    payload = smi_workbench.get_workbench_status()
    music = payload["release_evidence"]["music"]
    assert music["inspect_url"] == "/mission/workbench/music/release-evidence"
    assert music["founder_only"] is True
    assert music["read_only"] is True
    assert music["inspected_in_this_request"] is False
    assert music["production_certified"] is False
    assert music["migration_performed"] is False


def test_music_release_evidence_requires_authentication(anonymous_client):
    response = anonymous_client.get("/mission/workbench/music/release-evidence")
    assert response.status_code == 401
    assert response.get_json()["error"]["code"] == "authentication_required"


def test_music_release_evidence_denies_non_founder(client, monkeypatch):
    monkeypatch.setattr(
        web_security, "private_authority_allowed", lambda user: False
    )
    response = client.get("/mission/workbench/music/release-evidence")
    assert response.status_code == 403
    assert response.get_json()["error"]["code"] == "human_authority_required"


def test_music_release_evidence_fails_closed_without_store(client, monkeypatch):
    monkeypatch.setattr(
        web_security, "private_authority_allowed", lambda user: True
    )
    monkeypatch.setattr(
        music_civilization_migration,
        "inspect",
        lambda: (_ for _ in ()).throw(RuntimeError("postgresql://private-secret")),
    )
    response = client.get("/mission/workbench/music/release-evidence")
    assert response.status_code == 503
    payload = response.get_json()
    assert payload["inspection_available"] is False
    assert payload["schema_inventory_ready"] is False
    assert payload["production_certified"] is False
    assert payload["migration_performed"] is False
    assert "private-secret" not in response.get_data(as_text=True)


def test_music_release_evidence_founder_receives_read_only_inventory(client, monkeypatch):
    monkeypatch.setattr(
        web_security, "private_authority_allowed", lambda user: True
    )
    monkeypatch.setattr(
        music_civilization_migration,
        "inspect",
        lambda: {
            "registry_present": True,
            "base_product_core_present": True,
            "existing": ["0007_oap_music_evidence_chain"],
            "pending": ["0008_oap_radio_core"],
            "checksum_mismatches": [],
            "schema_inventory_ready": False,
            "migration_performed": False,
            "human_approval_granted": False,
        },
    )
    response = client.get("/mission/workbench/music/release-evidence")
    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    payload = response.get_json()
    assert payload["inspection_available"] is True
    assert payload["pending"] == ["0008_oap_radio_core"]
    assert payload["production_certified"] is False
    assert payload["live_browser_proven"] is False
    assert payload["migration_performed"] is False
