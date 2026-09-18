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
    assert snapshot["generation_backend_configured"] is False
    assert snapshot["generation_runtime_proven"] is False
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


def test_studio_backend_status_is_secret_free(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "secret-test-value")
    snapshot = studio_intelligence.studio_media_backend.status()

    assert snapshot["configured"] is True
    assert snapshot["provider"] == "openai"
    assert snapshot["provider_is_authority"] is False
    assert "secret-test-value" not in str(snapshot)


def test_execute_imagine_promotes_only_real_artifact(monkeypatch):
    monkeypatch.setattr(
        studio_intelligence.studio_media_backend,
        "generate_image",
        lambda prompt: {
            "kind": "image",
            "model": "gpt-image-2",
            "mime_type": "image/png",
            "b64_json": "ZmFrZQ==",
            "artifact_proven": True,
            "provider_is_authority": False,
        },
    )
    monkeypatch.setattr(
        studio_intelligence.smi_receipt_backend,
        "write_receipt",
        lambda kind, payload: {
            "ok": True,
            "receipt_kind": kind,
            "receipt_id": "studio-image",
            "read_back_ok": True,
        },
    )

    result = studio_intelligence.execute_generation(
        "imagine",
        prompt="OAP world at sunrise",
    )

    assert result["state"] == "generated"
    assert result["output_generated"] is True
    assert result["artifact"]["artifact_proven"] is True
    assert result["execution_granted"] is False


def test_scene_builder_stays_purple_while_video_is_queued(monkeypatch):
    monkeypatch.setattr(
        studio_intelligence.studio_media_backend,
        "create_video",
        lambda prompt, source_image_data="": {
            "kind": "video_job",
            "id": "video_test",
            "model": "sora-2",
            "status": "queued",
            "progress": 0,
            "artifact_proven": False,
            "provider_is_authority": False,
        },
    )
    captured = {}
    monkeypatch.setattr(
        studio_intelligence.smi_receipt_backend,
        "write_receipt",
        lambda kind, payload: captured.setdefault("receipt", {"kind": kind, "payload": payload}),
    )

    result = studio_intelligence.execute_generation(
        "scene_builder",
        prompt="A short OAP local-first scene",
    )

    assert result["state"] == "provider_job_started"
    assert result["output_generated"] is False
    assert result["artifact"]["status"] == "queued"
    assert captured["receipt"]["payload"]["signal"] == "🟣"
    assert result["execution_granted"] is False


def test_studio_routes_are_founder_only_and_fail_closed():
    views = (ROOT / "mission_control" / "views.py").read_text()

    assert '@bp.post("/studio/generate")' in views
    assert '@bp.get("/studio/video/<video_id>/status")' in views
    assert '@bp.get("/studio/video/<video_id>/content")' in views
    assert views.count("login_required(api=True, founder_only=True)") >= 4
    assert "csrf_valid(request)" in views
    assert "studio_generation_unavailable" in views


def test_completed_video_status_can_promote_with_receipt(monkeypatch):
    monkeypatch.setattr(
        studio_intelligence.studio_media_backend,
        "video_status",
        lambda video_id: {
            "kind": "video_job",
            "id": video_id,
            "model": "sora-2",
            "status": "completed",
            "progress": 100,
            "artifact_proven": True,
            "content_path": f"/videos/{video_id}/content",
            "provider_is_authority": False,
        },
    )
    captured = {}
    monkeypatch.setattr(
        studio_intelligence.smi_receipt_backend,
        "write_receipt",
        lambda kind, payload: captured.setdefault("receipt", {"kind": kind, "payload": payload}),
    )

    result = studio_intelligence.generation_status("video_test")

    assert result["state"] == "generated"
    assert result["output_generated"] is True
    assert result["artifact"]["artifact_proven"] is True
    assert captured["receipt"]["payload"]["signal"] == "🟢"
    assert captured["receipt"]["payload"]["green_gate"] == "artifact_proven"
    assert result["execution_granted"] is False


def test_generation_content_requires_completion_then_returns_proven_bytes(monkeypatch):
    monkeypatch.setattr(
        studio_intelligence,
        "generation_status",
        lambda video_id: {
            "output_generated": True,
            "artifact": {"id": video_id, "status": "completed", "artifact_proven": True},
        },
    )
    monkeypatch.setattr(
        studio_intelligence.studio_media_backend,
        "video_content",
        lambda video_id: {
            "id": video_id,
            "mime_type": "video/mp4",
            "content": b"video-bytes",
            "artifact_proven": True,
            "provider_is_authority": False,
        },
    )

    artifact = studio_intelligence.generation_content("video_test")
    assert artifact["artifact_proven"] is True
    assert artifact["content"] == b"video-bytes"
    assert artifact["mime_type"] == "video/mp4"


def test_generation_content_fails_closed_before_completion(monkeypatch):
    monkeypatch.setattr(
        studio_intelligence,
        "generation_status",
        lambda video_id: {
            "output_generated": False,
            "artifact": {"id": video_id, "status": "in_progress", "artifact_proven": False},
        },
    )
    try:
        studio_intelligence.generation_content("video_test")
    except RuntimeError as exc:
        assert str(exc) == "studio_generation_artifact_not_ready"
    else:
        raise AssertionError("Video content must stay locked until completion proof.")
