from pathlib import Path

from mission_control import studio_intelligence

ROOT = Path(__file__).resolve().parents[1]


def test_studio_exposes_eight_first_party_workspaces():
    status = studio_intelligence.status()
    ids = [item["id"] for item in status["workspaces"]]
    assert ids == ["build", "data", "code", "fast", "motion", "music", "omni", "research"]
    assert status["first_party_workspace_identity"] is True
    assert status["copies_provider_branding"] is False
    assert status["music_audio_generation_proven"] is False


def test_workspace_profiles_preserve_governance_and_speed_semantics():
    assert studio_intelligence.workspace("build")["code_mode"] is True
    assert studio_intelligence.workspace("code")["thinking_level"] == "deep_dive"
    assert studio_intelligence.workspace("fast")["thinking_level"] == "instant"
    assert studio_intelligence.workspace("motion")["studio_mode"] is True
    assert studio_intelligence.workspace("music")["studio_mode"] is True
    assert studio_intelligence.workspace("omni")["thinking_level"] == "auto"
    assert "Do not copy another provider" in studio_intelligence.workspace_instruction("build")


def test_live_controller_submits_studio_workspace_and_ui_has_all_controls():
    controller = (ROOT / "mission_control" / "static" / "smi_canonical_controller.js").read_text()
    final = (ROOT / "mission_control" / "static" / "smi_chat_final.js").read_text()
    views = (ROOT / "mission_control" / "views.py").read_text()
    facade = (ROOT / "mission_control" / "smi_chat_runtime.py").read_text()
    core = (ROOT / "mission_control" / "smi_chat_runtime_core.py").read_text()

    assert "studio_workspace:selectedStudioWorkspace" in controller
    assert 'studio_workspace=str(payload.get("studio_workspace") or "auto")' in views
    assert 'studio_workspace: str = "auto"' in facade
    assert 'studio_workspace: str = "auto"' in core
    assert 'brain["studio_workspace"]' in core
    for workspace_id in ("build","data","code","fast","motion","music","omni","research"):
        assert f'["{workspace_id}"' in final
    assert "OAP_SMI_STUDIO_WORKSPACE" in final
