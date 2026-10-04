from __future__ import annotations

import re
from pathlib import Path

import app as app_module

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "mission_control" / "templates" / "ollama_chat_base.html"
FINAL = ROOT / "mission_control" / "static" / "smi_chat_final.js"
CANONICAL = ROOT / "mission_control" / "static" / "smi_canonical_controller.js"
INTERACTION = ROOT / "mission_control" / "static" / "smi_interaction_layer.js"
COMMAND = ROOT / "mission_control" / "static" / "smi_command_centre.js"

DIRECT_CONTROL_IDS = {
    "refresh-history",
    "new-chat",
    "live-character-toggle",
    "remove-image",
    "remove-media",
    "plus-button",
    "image-button",
    "file-button",
    "studio-button",
    "voice-reply-menu-button",
    "smi-settings-button",
    "reset-device-preferences",
    "saved-work-button",
    "code-button",
    "speaker-button",
    "mic-button",
    "pause-button",
    "stop-button",
    "send",
    "smi-map-close",
}


def test_every_direct_smi_button_has_runtime_owner():
    base = BASE.read_text(encoding="utf-8")
    scripts = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (FINAL, CANONICAL, INTERACTION, COMMAND)
    )
    inline = base.split("<script>", 1)[1] if "<script>" in base else ""

    button_ids = set(re.findall(r"<button\b[^>]*\bid=\"([^\"]+)\"", base))
    direct = {
        button_id
        for button_id in button_ids
        if button_id not in {"render", "github", "neon"}
    }

    assert direct == DIRECT_CONTROL_IDS
    for button_id in direct:
        assert button_id in scripts or button_id in inline, button_id


def test_every_smi_map_tab_target_is_registered_for_get():
    base = BASE.read_text(encoding="utf-8")
    targets = set(re.findall(r'data-map-view="([^"]+)"', base))
    adapter = app_module.app.url_map.bind("localhost")

    assert targets == {
        "/on-any-place",
        "/movement",
        "/travel/direct",
        "/map-intelligence/status",
    }
    for target in targets:
        endpoint, _ = adapter.match(target, method="GET")
        assert endpoint


def test_master_tool_actions_and_connectors_have_one_known_dispatch_family():
    base = BASE.read_text(encoding="utf-8")
    final = FINAL.read_text(encoding="utf-8")

    actions = set(re.findall(r'data-oap-action="([^"]+)"', base))
    connectors = set(re.findall(r'data-connector-id="([^"]+)"', base))

    for action in actions:
        assert f"id==='{action}'" in final, action
    assert connectors == {"render", "github", "neon"}
    assert "qa('[data-connector-id]').forEach" in final
