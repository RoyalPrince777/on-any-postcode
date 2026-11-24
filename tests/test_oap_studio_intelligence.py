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


def test_studio_exposes_canonical_generation_editing_tools_and_21_stages():
    snapshot = studio_intelligence.status()

    assert [tool["id"] for tool in snapshot["generation_tools"]] == [
        "imagine",
        "edit_image",
        "refine_image",
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
    assert views.count("login_required(api=True, founder_only=True)") >= 3
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


def test_studio_machine_scope_uses_real_dependency_state(monkeypatch):
    monkeypatch.setattr(
        studio_intelligence.studio_media_backend,
        "status",
        lambda: {
            "configured": True,
            "provider": "openai",
            "image_model": "gpt-image-2",
            "video_model": "sora-2",
        },
    )
    monkeypatch.setattr(
        studio_intelligence.smi_founder_assets,
        "schema_status",
        lambda: {"schema_ready": True, "error": None},
    )
    monkeypatch.setattr(
        studio_intelligence.smi_receipt_backend,
        "backend_configuration_status",
        lambda: {"durable_backend_configured": True},
    )
    state = studio_intelligence.status()
    assert state["machine_dependencies_configured"] is True
    assert state["machine_scope_complete"] is True
    assert state["full_live_certificate"] is False
    assert state["full_live_certificate_reason"] == "real_generated_artifact_receipt_required"


def test_public_studio_has_no_fake_percentage_unlock_copy():
    page = (ROOT / "templates" / "studio_public.html").read_text()
    assert "unlock at 75%" not in page
    assert "＋ Files" in page
    assert "🎙 Voice" in page
    assert "Files are available only in the signed-in private workspace" in page
    assert "Voice is available only in the signed-in private workspace" in page


def test_studio_ui_sends_owner_context_for_generated_artifact_indexing():
    final = (ROOT / "mission_control" / "static" / "smi_chat_final.js").read_text()
    assert "conversation_id:conversationId" in final
    assert "studio_request_id:" in final
    assert "Founder Library indexed" in final


def test_edit_and_refine_use_high_fidelity_source_reference(monkeypatch):
    calls = []

    def fake_edit(prompt, *, source_image_data, input_fidelity="high", size="auto"):
        calls.append(
            {
                "prompt": prompt,
                "source": source_image_data,
                "input_fidelity": input_fidelity,
            }
        )
        return {
            "kind": "image",
            "model": "gpt-image-2",
            "mime_type": "image/png",
            "b64_json": "ZmFrZQ==",
            "artifact_proven": True,
            "provider_is_authority": False,
            "input_fidelity": input_fidelity,
            "source_reference_used": True,
        }

    monkeypatch.setattr(studio_intelligence.studio_media_backend, "edit_image", fake_edit)
    monkeypatch.setattr(
        studio_intelligence.smi_receipt_backend,
        "write_receipt",
        lambda kind, payload: {"receipt_id": "edit-proof", "payload": payload},
    )
    source = "data:image/png;base64,ZmFrZQ=="

    edited = studio_intelligence.execute_generation(
        "edit_image",
        prompt="Change the background to a jungle waterfall.",
        source_image_data=source,
        character_lock=True,
    )
    refined = studio_intelligence.execute_generation(
        "refine_image",
        source_image_data=source,
        character_lock=True,
    )

    assert edited["output_generated"] is True
    assert edited["character_lock"] is True
    assert edited["source_reference_used"] is True
    assert refined["output_generated"] is True
    assert len(calls) == 2
    assert all(call["input_fidelity"] == "high" for call in calls)
    assert all(call["source"] == source for call in calls)
    assert "same primary character identity" in calls[0]["prompt"]
    assert "premium cinematic quality" in calls[1]["prompt"]


def test_character_lock_fails_closed_without_reference(monkeypatch):
    monkeypatch.setattr(
        studio_intelligence.smi_receipt_backend,
        "write_receipt",
        lambda kind, payload: {"receipt_id": "unused"},
    )
    try:
        studio_intelligence.execute_generation(
            "imagine",
            prompt="Create another scene.",
            character_lock=True,
        )
    except ValueError as exc:
        assert str(exc) == "studio_character_lock_requires_source_image"
    else:
        raise AssertionError("Character lock must fail closed without a source image.")


def test_studio_media_backend_has_real_edit_endpoint_contract():
    media = (ROOT / "mission_control" / "studio_media_backend.py").read_text()
    assert '"/images/edits"' in media
    assert '"images": [{"image_url": source}]' in media
    assert '"input_fidelity": fidelity' in media
    assert '"output_format": "png"' in media


def test_factory_combines_existing_studio_without_execution_escalation():
    snapshot = studio_intelligence.status()
    factory = snapshot["factory"]
    assert snapshot["id"] == "oap-studio-intelligence"
    assert factory["name"] == "OAP Factory"
    assert factory["authority_origin"] == "founder"
    assert factory["controller"] == "SMI"
    assert factory["access_hierarchy"] == (
        "founder_master_control",
        "smi_command_centre",
        "oap_factory",
        "my_oap_world_members_creators",
        "public_oap_world",
    )
    assert factory["one_canonical_studio"] is True
    assert factory["public_access_is_permission_scoped"] is True
    assert factory["public_inherits_founder_authority"] is False
    assert factory["founder_private_assets_public"] is False
    assert factory["public_media_generation_proven"] is False
    assert factory["creative_division"] == snapshot["id"]
    assert factory["factory_is_second_studio_engine"] is False
    assert factory["factory_is_separate_auth_system"] is False
    assert factory["capability_truth"]["character_swap"] == "preparation_only"
    assert factory["creative_tools"] == [tool["id"] for tool in snapshot["generation_tools"]]
    assert factory["guardian_required"] is True
    assert factory["hrm_required"] is True
    assert factory["stop_available"] is True
    assert factory["execution_granted"] is False
    assert factory["payment_authorised"] is False
    assert factory["publishing_granted"] is False
    assert factory["deployment_authorised"] is False
    assert factory["founder_final"] is True


def test_south_london_animation_recipe_is_provenance_safe():
    recipe = studio_intelligence.status()["animation_recipe"]
    assert recipe["width"] == 676
    assert recipe["height"] == 376
    assert recipe["frame_count"] == 6
    assert recipe["frame_duration_ms"] == 140
    assert recipe["total_duration_ms"] == 840
    assert recipe["rendering_origin"] == "chatgpt_image_generation_not_smi"
    assert recipe["render_verified_in_smi"] is False
    assert recipe["identity_lock"] == "approved_reference_required"
    assert recipe["replay_requires_owned_gif"] is True
    assert recipe["founder_review_required"] is True



def test_project_shell_preflight_reuses_studio_without_media_submission(monkeypatch):
    from mission_control import studio_project_shell

    monkeypatch.setattr(studio_project_shell.studio_media_backend,
                        "status", lambda: {"configured": False})
    status = studio_project_shell.status()
    assert status["approved_reference_available_in_smi"] is False
    assert status["generated_mp4_proven"] is False
    assert len(status["scenes"]) == 3
    assert status["renderer_configured"] is False
    scene = studio_project_shell.prepare("01", ratio="16:9", fps_target=60,
                                         reference_attached=True)
    assert scene["scene_name"] == "Quad Arrival"
    assert scene["video_size"] == "1280x720"
    assert scene["video_seconds"] == "8"
    assert scene["fps_target"] == 60
    assert "black-and-gold OAP quad" in scene["prompt"]
    assert "You lot thought nobody was watching" in scene["prompt"]
    assert scene["renderer_contact_verified"] is False
    assert scene["voice_sync_verified"] is False
    assert scene["can_request_render"] is False
    assert scene["blocked_reason"] == "renderer_unconfigured"
    assert scene["render_submitted"] is False
    assert scene["artifact_proven"] is False
    assert scene["paid_submission_authorised"] is False
    assert scene["founder_final_required"] is True


def test_project_shell_requires_reference_and_limits_scene_options(monkeypatch):
    import pytest

    from mission_control import studio_project_shell

    monkeypatch.setattr(studio_project_shell.studio_media_backend,
                        "status", lambda: {"configured": True})
    plan = studio_project_shell.prepare(
        "03", ratio="9:16", fps_target=24, reference_attached=False,
    )
    assert plan["video_size"] == "720x1280"
    assert plan["blocked_reason"] == "approved_reference_required"
    assert plan["can_request_render"] is False
    ready_to_request = studio_project_shell.prepare(
        "02", ratio="16:9", fps_target=30, reference_attached=True,
    )
    assert ready_to_request["can_request_render"] is True
    assert ready_to_request["render_submitted"] is False
    assert ready_to_request["identity_continuity_verified"] is False
    assert ready_to_request["fps_verified"] is False
    for scene, ratio, fps, reference in (
        ("99", "16:9", 60, True),
        ("01", "1:1", 60, True),
        ("01", "16:9", 120, True),
        ("01", "16:9", True, True),
        ("01", "16:9", "30.0", True),
        ("01", "16:9", 60, "yes"),
    ):
        with pytest.raises((TypeError, ValueError)):
            studio_project_shell.prepare(
                scene, ratio=ratio, fps_target=fps, reference_attached=reference,
            )


def test_project_shell_actual_ratio_is_forwarded_to_canonical_renderer(monkeypatch):
    from mission_control import studio_media_backend

    received = {}

    def fake_render(path, fields, *, file_field=None):
        received.update({"path": path, "fields": fields, "file_field": file_field})
        return {"id": "video_project_shell", "status": "queued", "progress": 0}

    monkeypatch.setattr(studio_media_backend, "_multipart_call", fake_render)
    result = studio_media_backend.create_video(
        "PROJECT SHELL verified request", seconds="8", size="1280x720",
    )
    assert received["path"] == "/videos"
    assert received["fields"]["size"] == "1280x720"
    assert received["fields"]["seconds"] == "8"
    assert result["artifact_proven"] is False
    assert result["status"] == "queued"


def test_project_shell_video_size_errors_do_not_call_provider(monkeypatch):
    import pytest

    from mission_control import studio_media_backend

    def unsafe(*args, **kwargs):
        raise AssertionError("Provider must not be called for invalid options")

    monkeypatch.setattr(studio_media_backend, "_multipart_call", unsafe)
    for size, seconds in (
        ("9999x9999", "8"), ("720x1280", "5"), ("16:9", "4"),
    ):
        with pytest.raises(ValueError):
            studio_media_backend.create_video(
                "Original approved brief", size=size, seconds=seconds,
            )


def test_project_shell_smi_ui_is_founder_only_and_reuses_existing_media_tool():
    template = (ROOT / "mission_control" / "templates" / "ollama_chat.html").read_text()
    views = (ROOT / "mission_control" / "views.py").read_text()
    js = (ROOT / "mission_control" / "static" / "smi_project_shell.js").read_text()
    final_js = (ROOT / "mission_control" / "static" / "smi_chat_final.js").read_text()
    assert "projectShellPrepareUrl:" in template
    assert "smi_project_shell.js" in template
    assert "smi_project_shell.css" in template
    assert '@bp.post("/studio/project-shell/prepare")' in views
    assert "def smi_studio_project_shell_prepare" in views
    assert "login_required(api=True, founder_only=True)" in views
    assert "web_security.csrf_valid(request)" in views
    assert "data-shell-consent" in js
    assert "data-shell-prepare" in js
    assert "referenceAttached()" in js
    assert "data-shell-render disabled" in js
    assert "OAP_SMI_PENDING_PROJECT_SHELL" in js
    assert 'data-studio-tool="scene_builder"' in js
    assert "window.OAP_SMI_PENDING_PROJECT_SHELL" in final_js
    assert "video_size:projectShell.video_size" in final_js
    assert "video_seconds:projectShell.video_seconds" in final_js
    assert "rendered" not in js.lower() or "unverified" in js.lower()
    assert "No render submitted" in js


def test_factory_scene_01_exact_timeline_stays_unrendered():
    plan = studio_intelligence.factory_structure()["scene_01_plan"]
    shots = plan["shots"]
    assert len(shots) == 7
    assert plan["duration_ms"] == 21000
    assert (plan["master_width"], plan["master_height"]) == (1920, 1080)
    assert plan["master_fps"] == 24
    assert plan["master_frame_count"] == 504
    assert plan["cinematic_quality_verified"] is False
    assert all(shot["camera_move"] and shot["lens_mm_target"] for shot in shots)
    assert sum(shot["provider_seconds"] * 1000 for shot in shots) == plan["source_duration_ms"]
    for index, shot in enumerate(shots):
        assert shot["start_ms"] == index * 3000
        assert shot["end_ms"] == (index + 1) * 3000
        assert shot["provider_seconds"] == 4
        assert shot["trim_end_ms"] - shot["trim_start_ms"] == 3000
        assert shot["artifact_verified"] is False
    assert plan["approved_reference_required"] is True
    assert plan["location_reference_required"] is True
    assert plan["guardian_required"] is True
    assert plan["hrm_required"] is True
    assert plan["founder_final"] is True
    for key in ("render_submitted", "artifact_verified", "composition_verified",
                "execution_granted", "payment_authorised", "publishing_granted"):
        assert plan[key] is False
