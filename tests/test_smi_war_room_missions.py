"""Draft-only contract and preservation proof for the additive SMI War Room."""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "mission_control/templates/ollama_chat_base.html"
WRAPPER = ROOT / "mission_control/templates/ollama_chat.html"
COMMAND = ROOT / "mission_control/static/smi_command_centre.js"
MISSIONS = ROOT / "mission_control/static/smi_war_room_missions.js"


def test_war_room_loads_after_canonical_chat_and_command_centre():
    wrapper = WRAPPER.read_text(encoding="utf-8")
    assert wrapper.index("smi_canonical_controller.js") < wrapper.index(
        "smi_command_centre.js"
    ) < wrapper.index("smi_war_room_missions.js")
    assert wrapper.count("smi_war_room_missions.js") == 1
    assert wrapper.count("smi_war_room_missions.css") == 1
    assert "visibleLiveStatus:false" in wrapper


def test_existing_chat_handlers_character_and_uploads_are_preserved():
    base = BASE.read_text(encoding="utf-8")
    command = COMMAND.read_text(encoding="utf-8")
    mission = MISSIONS.read_text(encoding="utf-8")
    for control in (
        'id="messages"',
        'id="chat-form"',
        'id="message"',
        'id="plus-button"',
        'id="attach-menu"',
        'id="image-input"',
        'id="media-input"',
        'id="stop-button"',
        'id="smi-character"',
        'id="history-list"',
    ):
        assert control in base
    assert 'document.createComment("original SMI character position")' in command
    assert 'if(marker.parentNode)marker.parentNode.insertBefore(character,marker)' in command
    assert 'new Event("input", {bubbles:true})' in mission
    assert 'composer.value = prompt;' in mission
    assert 'composer.value.trim()' in mission
    assert 'composer.focus()' in mission
    assert 'requestSubmit(' not in mission
    assert 'fetch(' not in mission
    assert 'localStorage' not in mission
    assert 'sessionStorage' not in mission
    assert "data-war-approval" in mission


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js required")
def test_multi_select_contract_and_fail_closed_build_scope():
    source = MISSIONS.as_posix()
    program = r"""
const fs = require("fs");
global.window = {};
global.document = {getElementById: () => null};
eval(fs.readFileSync(process.argv[1], "utf8"));
const api = window.OAP_SMI_WAR_ROOM_MISSIONS;
const make = (overrides = {}) => api.buildContract({
  selected:["centre","hrm","hrm","egress"],depth:21,
  mode:"review",instruction:"Preserve every chat",approved:false,...overrides
});
const prompt = make();
if (!prompt.includes("MAIN FOUNDER MISSION: Preserve every chat")) throw Error("founder mission missing");
if (prompt.match(/HRM rollback/g).length !== 1) throw Error("duplicate mission");
if (!prompt.includes("External egress") || !prompt.includes("21 denominated signals")) throw Error("contract incomplete");
if (!prompt.includes("Review/simulation only; no repository writes or tests.")) throw Error("review scope lost");
if (prompt.includes("Draft-only changes and tests approved")) throw Error("false authorisation");
for (const patch of [
  {selected:[]},{selected:["unknown"]},{depth:4},{mode:"execute"},
  {mode:"build",approved:false}
]) {
  let failed = false;
  try { make(patch); } catch { failed = true; }
  if (!failed) throw Error("invalid or unapproved action accepted");
}
if (!make({mode:"build",approved:true}).includes("no merge or deployment")) throw Error("release guard lost");
console.log("war_room_contract_passed");
"""
    run = subprocess.run(
        ["node", "-e", program, source],
        capture_output=True,
        text=True,
        timeout=12,
        check=False,
    )
    assert run.returncode == 0, run.stderr
    assert "war_room_contract_passed" in run.stdout
