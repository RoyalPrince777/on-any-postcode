from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_smi_chat_control_surface_is_permanent():
    base = (ROOT / "mission_control" / "templates" / "ollama_chat_base.html").read_text()
    for marker in (
        'id="pause-button"',
        'id="stop-button"',
        'id="speaker-button"',
        'id="thinking-level"',
        'value="auto"',
        'value="manual"',
        'value="instant"',
        'value="think"',
        'value="deep_dive"',
        'value="war_room"',
        'data-connector-id="render"',
        'data-connector-id="github"',
        'data-connector-id="neon"',
        'id="studio-button"',
        'data-oap-action="war-room"',
        'data-oap-action="button-proof"',
        'data-oap-action="signals-21"',
        'data-oap-action="guardian"',
        'data-oap-action="routes"',
        'data-oap-action="brain"',
        'data-oap-action="agents"',
        'data-oap-action="infrastructure"',
        'data-oap-action="judgement"',
        'data-oap-action="function-health"',
        'data-oap-action="green-gate"',
        'data-oap-action="hrm"',
        'data-oap-action="improvement"',
        'data-oap-action="swot"',
        'data-oap-action="behaviour"',
        'data-oap-action="github-governed"',
    ):
        assert marker in base


def test_smi_feedback_and_studio_routes_are_exposed():
    views = (ROOT / "mission_control" / "views.py").read_text()
    wrapper = (ROOT / "mission_control" / "templates" / "ollama_chat.html").read_text()
    assert '@bp.post("/chat/feedback")' in views
    assert '@bp.get("/studio/status")' in views
    assert "feedbackUrl:" in wrapper
    assert "studioStatusUrl:" in wrapper
    assert "studioGenerateUrl:" in wrapper
    assert "studioVideoStatusUrlTemplate:" in wrapper
    assert "studioVideoContentUrlTemplate:" in wrapper


def test_smi_runtime_modes_reach_governed_brain_context():
    core = (ROOT / "mission_control" / "smi_chat_runtime_core.py").read_text()
    facade = (ROOT / "mission_control" / "smi_chat_runtime.py").read_text()
    for marker in (
        'thinking_level: str = "auto"',
        'studio_mode: bool = False',
        'brain["thinking_level"] = level',
        'brain["studio_mode"] = resolved_studio_mode',
        'brain["resolved_depth"] = resolved_depth',
        '"instant": 650',
        '"think": 1100',
        '"deep_dive": 1800',
    ):
        assert marker in core
    assert "thinking_level=thinking_level" in facade
    assert "studio_mode=studio_mode" in facade


def test_smi_response_actions_include_feedback_and_voice():
    script = (ROOT / "mission_control" / "static" / "smi_chat_final.js").read_text()
    for marker in (
        "feedbackUrl",
        "'helpful'",
        "'not_helpful'",
        "SpeechSynthesisUtterance",
        "studioStatusUrl",
        "githubAction()",
        "Run SWOT Intelligence on:",
        "Run Behaviour Intelligence on:",
        "21 dimensions · evidence-backed percentages only",
        "Strengths · Weaknesses · Opportunities · Threats · Practical Move",
    ):
        assert marker in script


def test_smi_auto_resolves_smallest_sufficient_depth_and_studio():
    from mission_control import smi_chat_runtime_core as core

    level, studio, depth = core._auto_runtime_mode(
        "hello",
        requested_level="auto",
        studio_mode=False,
        code_mode=False,
        image_attached=False,
        media_kind=None,
        war_room_triggered=False,
    )
    assert (level, studio, depth) == ("instant", False, 3)

    level, studio, depth = core._auto_runtime_mode(
        "Analyse this attached image",
        requested_level="auto",
        studio_mode=False,
        code_mode=False,
        image_attached=True,
        media_kind="image",
        war_room_triggered=False,
    )
    assert (level, studio, depth) == ("think", False, 7)

    level, studio, depth = core._auto_runtime_mode(
        "Imagine a postcode world at sunrise",
        requested_level="auto",
        studio_mode=False,
        code_mode=False,
        image_attached=False,
        media_kind=None,
        war_room_triggered=False,
    )
    assert (level, studio, depth) == ("deep_dive", True, 21)


def test_explicit_smi_depth_is_preserved_but_generation_can_auto_enter_studio():
    from mission_control import smi_chat_runtime_core as core

    level, studio, depth = core._auto_runtime_mode(
        "Scene Builder: create a short local-first scene",
        requested_level="think",
        studio_mode=False,
        code_mode=False,
        image_attached=False,
        media_kind=None,
        war_room_triggered=False,
    )
    assert (level, studio, depth) == ("think", True, 7)


def test_smi_auto_deepens_for_code_war_room_and_recovery():
    from mission_control import smi_chat_runtime_core as core

    for kwargs in (
        {"code_mode": True, "war_room_triggered": False, "message": "review this"},
        {"code_mode": False, "war_room_triggered": True, "message": "review this"},
        {"code_mode": False, "war_room_triggered": False, "message": "recovery architecture"},
    ):
        level, _studio, depth = core._auto_runtime_mode(
            kwargs["message"],
            requested_level="auto",
            studio_mode=False,
            code_mode=kwargs["code_mode"],
            image_attached=False,
            media_kind=None,
            war_room_triggered=kwargs["war_room_triggered"],
        )
        assert (level, depth) == ("deep_dive", 21)



def test_smi_interaction_layer_exposes_canonical_modes_and_capture_paths():
    wrapper = (ROOT / "mission_control" / "templates" / "ollama_chat.html").read_text()
    script = (ROOT / "mission_control" / "static" / "smi_interaction_layer.js").read_text()
    dashboard = (
        ROOT / "mission_control" / "static" / "smi_sovereign_dashboard.js"
    ).read_text()

    for marker in (
        'id="chat-mode-button"',
        'id="voice-mode-button"',
        'id="vision-button"',
        'id="faceup-button"',
        'id="screen-mode-button"',
        'id="tools-mode-button"',
        'getUserMedia',
        'getDisplayMedia',
        'Face Up',
        'Screen Intelligence capture',
        'SMI Vision camera capture',
        '["manual", "Manual"]',
        '["instant", "3"]',
        '["think", "7"]',
        '["deep_dive", "21"]',
        '["war_room", "War Room"]',
    ):
        assert marker in script

    assert "smi_interaction_layer.js" in wrapper
    assert "smi_interaction_layer.css" in wrapper
    assert "smi-status-open" in dashboard
    assert "smi-dashboard-mode" not in dashboard
    assert "smi-chat-mode" not in dashboard


def test_manual_and_explicit_war_room_modes_preserve_governance():
    from mission_control import smi_chat_runtime_core as core

    level, studio, depth = core._auto_runtime_mode(
        "review this",
        requested_level="manual",
        studio_mode=False,
        code_mode=False,
        image_attached=False,
        media_kind=None,
        war_room_triggered=False,
    )
    assert (level, studio, depth) == ("manual", False, 3)

    level, studio, depth = core._auto_runtime_mode(
        "review this",
        requested_level="war_room",
        studio_mode=False,
        code_mode=False,
        image_attached=False,
        media_kind=None,
        war_room_triggered=False,
    )
    assert (level, studio, depth) == ("deep_dive", False, 21)


def test_explicit_war_room_selector_forces_review_without_execution_authority():
    core = (ROOT / "mission_control" / "smi_chat_runtime_core.py").read_text()
    live_brain = (ROOT / "mission_control" / "live_brain.py").read_text()
    war_room = (ROOT / "oap" / "war_room" / "engine.py").read_text()

    assert 'force_war_room=requested_mode == "war_room"' in core
    assert "force_review=bool(force_war_room)" in live_brain
    assert "bool(force_review)" in war_room
    assert '"decision_authority": False' in live_brain
    assert '"mode": "simulation_only"' in war_room



def test_function_health_tracks_interaction_certification_without_fake_green():
    from mission_control import smi_function_health

    result = smi_function_health.interaction_certification()
    assert result["all_implemented_for_certification"] is True
    assert result["whole_interaction_green"] is False
    assert result["live_proof_required"] is True
    assert result["no_fake_green"] is True
    assert {item["id"] for item in result["surfaces"]} == {
        "chat",
        "voice",
        "vision",
        "face-up",
        "screen",
        "tools",
        "intelligence-selector",
        "runtime-controls",
    }
    assert all(item["state"] == "purple" for item in result["surfaces"])


def test_smi_auto_result_exposes_safe_resolved_depth():
    core = (ROOT / "mission_control" / "smi_chat_runtime_core.py").read_text()
    facade = (ROOT / "mission_control" / "smi_chat_runtime.py").read_text()
    canonical = (ROOT / "mission_control" / "static" / "smi_canonical_controller.js").read_text()
    assert '"resolved_depth": resolved_depth' in core
    assert '"auto_selected": bool(brain.get("auto_selected"))' in core
    assert 'enriched["requested_thinking_level"]' in facade
    assert 'enriched["resolved_depth"]' in facade
    assert "AUTO →" in canonical
