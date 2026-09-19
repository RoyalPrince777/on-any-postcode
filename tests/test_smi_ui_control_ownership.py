from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "mission_control" / "templates" / "ollama_chat_base.html"
WRAPPER = ROOT / "mission_control" / "templates" / "ollama_chat.html"
FINAL = ROOT / "mission_control" / "static" / "smi_chat_final.js"
CANONICAL = ROOT / "mission_control" / "static" / "smi_canonical_controller.js"
INTERACTION = ROOT / "mission_control" / "static" / "smi_interaction_layer.js"
DASHBOARD = ROOT / "mission_control" / "static" / "smi_sovereign_dashboard.js"
DASHBOARD_CSS = ROOT / "mission_control" / "static" / "smi_sovereign_dashboard.css"


def test_core_controls_have_one_execution_owner():
    base = BASE.read_text(encoding="utf-8")
    wrapper = WRAPPER.read_text(encoding="utf-8")
    final = FINAL.read_text(encoding="utf-8")
    canonical = CANONICAL.read_text(encoding="utf-8")

    assert "smi_canonical_controller.js" in wrapper
    assert "smi_request_guard.js" not in wrapper

    assert "form.addEventListener('submit',async" not in base
    assert "messageInput.addEventListener('keydown'" not in base
    assert "plusButton.onclick=" not in base
    assert "pauseButton.onclick=" not in base
    assert "stopButton.onclick=" not in base
    assert "speakerButton.onclick=" not in base
    assert "const Recognition=window.SpeechRecognition" not in base

    assert "input.addEventListener('keydown'" not in final

    assert canonical.count("oapForm.addEventListener('submit'") == 1
    assert canonical.count("oapInput.addEventListener('keydown'") == 1
    assert canonical.count("oapPlus.addEventListener('click'") == 1
    assert canonical.count("oapPause.addEventListener('click'") == 1
    assert canonical.count("oapStop.addEventListener('click'") == 1


def test_user_message_is_rendered_before_stream_starts():
    canonical = CANONICAL.read_text(encoding="utf-8")
    rendered = canonical.index("add(userLabel,'user')")
    fetch = canonical.index("await fetch(streamUrl")
    assert rendered < fetch


def test_all_master_tool_actions_have_handlers():
    base = BASE.read_text(encoding="utf-8")
    final = FINAL.read_text(encoding="utf-8")

    actions = set(re.findall(r'data-oap-action="([^"]+)"', base))
    connectors = set(re.findall(r'data-connector-id="([^"]+)"', base))

    assert actions == {
        "war-room",
        "function-health",
        "green-gate",
        "hrm",
        "founder-library",
        "improvement",
        "swot",
        "behaviour",
        "github-governed",
    }
    for action in actions:
        assert f"id==='{action}'" in final
    for connector in connectors:
        assert connector in {"render", "github", "neon"}
    assert "qa('[data-connector-id]').forEach" in final


def test_screen_controls_have_unique_ids():
    canonical = CANONICAL.read_text(encoding="utf-8")
    interaction = INTERACTION.read_text(encoding="utf-8")

    assert "screen-capture-button" in canonical
    assert 'id="screen-mode-button"' in interaction
    assert 'id="screen-button"' not in interaction
    assert "screen.id='screen-button'" not in canonical


def test_status_drawer_never_hides_chat_workspace():
    dashboard = DASHBOARD.read_text(encoding="utf-8")
    css = DASHBOARD_CSS.read_text(encoding="utf-8")

    assert "smi-status-open" in dashboard
    assert "smi-dashboard-mode" not in dashboard
    assert "smi-chat-mode" not in dashboard
    assert "smi-status-open .workspace-grid{display:grid!important}" in css
    assert "smi-status-open .smi-dashboard-layer{display:flex!important}" in css
