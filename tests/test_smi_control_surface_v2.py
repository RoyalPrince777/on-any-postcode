from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WRAPPER = ROOT / "mission_control" / "templates" / "ollama_chat.html"
FINAL = ROOT / "mission_control" / "static" / "smi_chat_final.js"
CHARACTER = ROOT / "mission_control" / "static" / "smi_live_character.css"
VIEWS = ROOT / "mission_control" / "views.py"
CORE = ROOT / "mission_control" / "smi_chat_runtime_core.py"
STUDIO = ROOT / "mission_control" / "studio_intelligence.py"
MEDIA = ROOT / "mission_control" / "studio_media_backend.py"
HEALTH = ROOT / "mission_control" / "smi_function_health.py"


def test_control_surface_uses_real_runtime_routes():
    wrapper = WRAPPER.read_text(encoding="utf-8")
    for marker in (
        "buttonProofUrl:",
        "studioGenerateUrl:",
        "studioVideoStatusUrl:",
        "studioVideoContentUrl:",
        "brainUrl:",
        "agentsUrl:",
        "infrastructureUrl:",
        "judgementUrl:",
    ):
        assert marker in wrapper


def test_button_proof_is_post_ack_not_click_only():
    views = VIEWS.read_text(encoding="utf-8")
    final = FINAL.read_text(encoding="utf-8")
    assert '@bp.post("/ui/button-proof")' in views
    assert '"click_only_proof": False' in views
    assert "status_code < 200 or status_code >= 400" in views
    assert "await recordButtonProof(actionId,target,response.status)" in final
    assert "clickOnlyProof:false" in final


def test_missing_intelligence_tools_are_added_to_master_tools():
    final = FINAL.read_text(encoding="utf-8")
    for tool_id in (
        "signals-21",
        "guardian",
        "routes",
        "brain",
        "agents",
        "infrastructure",
        "judgement",
    ):
        assert f'id:"{tool_id}"' in final
    assert "functionHealthSync:true" in final
    assert "Search SMI tools" in final


def test_studio_tools_execute_directly_and_completed_video_is_playable():
    final = FINAL.read_text(encoding="utf-8")
    views = VIEWS.read_text(encoding="utf-8")
    studio = STUDIO.read_text(encoding="utf-8")
    media = MEDIA.read_text(encoding="utf-8")
    for tool in ("imagine", "bring_alive", "scene_builder"):
        assert f'studioTool:"{tool}"' in final
    assert "cfg.studioGenerateUrl" in final
    assert "cfg.studioVideoStatusUrl" in final
    assert "cfg.studioVideoContentUrl" in final
    assert '@bp.get("/studio/video/<video_id>/content")' in views
    assert "def generation_content" in studio
    assert "def video_content" in media
    assert "MAX_VIDEO_BYTES" in media


def test_auto_depth_is_safe_completion_metadata_and_visible():
    core = CORE.read_text(encoding="utf-8")
    final = FINAL.read_text(encoding="utf-8")
    assert '"resolved_depth": int(brain.get("resolved_depth") or 3)' in core
    assert '"auto_selected": bool(brain.get("auto_selected"))' in core
    assert "AUTO resolved to " in final
    assert "autoDepthVisible:true" in final


def test_control_surface_stays_purple_until_live_browser_certification():
    health = HEALTH.read_text(encoding="utf-8")
    assert '"id": "control-surface-v2"' in health
    assert "signed-in browser/device certification is still required for full green" in health
    assert '"live_runtime_proven": False' in health


def test_character_has_merry_expressive_style_and_reduced_motion():
    css = CHARACTER.read_text(encoding="utf-8")
    for marker in (
        "smiMerryFloat",
        "smiSparkle",
        "smiBlink",
        "smiListenLean",
        "smiThinkTilt",
        "smiTalkBob",
        "prefers-reduced-motion",
    ):
        assert marker in css
