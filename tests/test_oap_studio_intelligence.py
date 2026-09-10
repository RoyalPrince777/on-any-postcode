from pathlib import Path

from mission_control import smi_workbench, studio_intelligence

ROOT = Path(__file__).resolve().parents[1]


def test_studio_contract_is_smi_powered_and_governed():
    status = studio_intelligence.status()

    assert status["id"] == "oap-studio-intelligence"
    assert status["name"] == "OAP Studio Intelligence"
    assert status["powered_by"] == "SMI"
    assert status["pipeline"] == [
        "Create",
        "Edit",
        "Package",
        "Rights",
        "Publish",
        "Distribute",
        "Campaign",
        "Analyse",
    ]
    governance = status["governance"]
    assert governance["human_authority_final"] is True
    assert governance["rights_proof_required"] is True
    assert governance["external_distribution_locked_until_proof"] is True
    assert governance["payment_authority_granted"] is False
    assert governance["publishing_authority_granted"] is False
    assert governance["execution_authority_granted"] is False


def test_founder_workbench_exposes_studio_without_secrets(monkeypatch):
    monkeypatch.setattr(
        smi_workbench.smi_chat_runtime,
        "health",
        lambda: {"status": "yellow", "checks": {"database": False, "schema": False}},
    )

    payload = smi_workbench.get_workbench_status()
    studio = next(
        item for item in payload["capabilities"] if item["id"] == "oap-studio-intelligence"
    )

    assert studio["ready"] is True
    assert studio["powered_by"] == "SMI"
    assert "OAP Studio Intelligence mode" in studio["activation_prompt"]
    assert "OAP Studio Intelligence planning and preparation" in payload["runtime_gate"]["available"]


def test_smi_plus_menu_launches_studio_without_public_founder_door():
    smi = (ROOT / "mission_control" / "templates" / "ollama_chat.html").read_text()
    spot = (ROOT / "mission_control" / "templates" / "spot.html").read_text()

    assert "data-oap-studio" in smi or "dataset.oapStudio" in smi
    assert "OAP Studio Intelligence" in smi
    assert "launchStudio" in smi
    assert "activation_prompt" in smi
    # Studio is a private Founder capability. Public Spot must not expose its private route.
    assert "https://oap-smi.onrender.com/founder" not in spot
    assert "🎬 OAP Studio Intelligence" not in spot
