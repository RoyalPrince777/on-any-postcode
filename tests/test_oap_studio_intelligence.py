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


def test_studio_is_canonical_media_engine_for_smi_chat_capture():
    status = studio_intelligence.status()
    alignment = status["alignment"]

    assert "SMI Chat" in status["entry_points"]
    assert "camera still" in status["capture_inputs"]
    assert "screen still" in status["capture_inputs"]
    assert alignment["smi_chat_is_entry_surface"] is True
    assert alignment["studio_is_canonical_media_engine"] is True
    assert alignment["duplicate_studio_engine_allowed"] is False
    assert alignment["capture_does_not_grant_execution"] is True


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


def test_smi_plus_menu_launches_studio():
    smi = (ROOT / "mission_control" / "templates" / "ollama_chat.html").read_text()

    assert "data-oap-studio" in smi or "dataset.oapStudio" in smi
    assert "OAP Studio Intelligence" in smi
    assert "launchStudio" in smi
    assert "activation_prompt" in smi


def test_studio_exposes_three_canonical_generation_tools_and_21_stages():
    snapshot = studio_intelligence.status()

    assert [tool["id"] for tool in snapshot["generation_tools"]] == [
        "imagine",
        "bring_alive",
        "scene_builder",
    ]
    assert snapshot["studio_21_stage_count"] == 21
    assert len(snapshot["studio_21_stages"]) == 21
    assert snapshot["generation_backend_proven"] is False
    assert snapshot["full_live_certificate"] is False


def test_studio_generation_job_is_21_stage_and_never_fakes_output(monkeypatch):
    captured = {}

    def fake_receipt(kind, payload):
        captured["kind"] = kind
        captured["payload"] = payload
        return {
            "ok": True,
            "receipt_kind": kind,
            "receipt_id": "studio-test",
            "read_back_ok": True,
            "durable": False,
        }

    monkeypatch.setattr(
        studio_intelligence.smi_receipt_backend,
        "write_receipt",
        fake_receipt,
    )

    result = studio_intelligence.prepare_generation(
        "imagine",
        prompt="A local-first OAP world scene",
    )

    assert result["smi_depth"] == 21
    assert len(result["stages"]) == 21
    assert result["state"] == "prepared"
    assert result["output_generated"] is False
    assert result["artifact"] is None
    assert result["next_gate"] == "media_generation_backend"
    assert result["execution_granted"] is False
    assert result["human_authority_final"] is True
    assert captured["kind"] == "studio_generation_receipt"
    assert captured["payload"]["gate"] == 21
    assert captured["payload"]["safe_payload"]["output_generated"] is False


def test_bring_alive_requires_an_image_reference():
    try:
        studio_intelligence.prepare_generation("bring_alive")
    except ValueError as exc:
        assert str(exc) == "studio_source_image_required"
    else:
        raise AssertionError("Bring Alive must fail closed without a source image.")
