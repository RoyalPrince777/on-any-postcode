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
        'value="instant"',
        'value="think"',
        'value="deep_dive"',
        'data-connector-id="render"',
        'data-connector-id="github"',
        'data-connector-id="neon"',
        'id="studio-button"',
        'data-oap-action="war-room"',
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


def test_smi_runtime_modes_reach_governed_brain_context():
    core = (ROOT / "mission_control" / "smi_chat_runtime_core.py").read_text()
    facade = (ROOT / "mission_control" / "smi_chat_runtime.py").read_text()
    for marker in (
        'thinking_level: str = "auto"',
        'studio_mode: bool = False',
        'brain["thinking_level"] = level',
        'brain["studio_mode"] = bool(studio_mode)',
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
