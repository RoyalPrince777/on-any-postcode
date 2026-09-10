import json
from pathlib import Path

from mission_control import smi_workbench


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

    assert [item["id"] for item in payload["connectors"]] == ["render", "github", "neon"]
    assert all(item["configured"] for item in payload["connectors"])
    assert "secret-value" not in serialized
    assert "postgresql://" not in serialized
    assert payload["governance"]["human_authority_final"] is True


def test_workbench_status_is_private(client):
    response = client.get("/mission/workbench/status")
    assert response.status_code in {302, 401, 404}


def test_personal_smi_has_quiet_tools_workbench():
    page = Path("mission_control/templates/ollama_chat.html").read_text(encoding="utf-8")
    assert "Quiet 2027 workbench" in page
    assert "Open connected tools" in page
    assert "Credentials are never shown" in page
    assert "workbenchUrl" in page
