from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "mission_control" / "templates" / "linkup.html"
SCRIPT = ROOT / "static" / "linkup_voice.js"


def test_linkup_surface_exposes_voice_without_unlocking_generic_share():
    template = TEMPLATE.read_text(encoding="utf-8")

    assert "linkup_voice.js" in template
    assert "data-oap-voice-control" in template
    assert "data-oap-voice-stop" in template
    assert "data-oap-voice-list" in template
    assert "data-oap-voice-status" in template
    assert "Share <small>locked</small>" in template
    assert "disabled data-runtime-locked" in template


def test_voice_controller_is_explicit_audio_only_same_origin_and_bounded():
    script = SCRIPT.read_text(encoding="utf-8")

    assert "navigator.mediaDevices.getUserMedia({ audio: true, video: false })" in script
    assert "new MediaRecorder" in script
    assert "MediaRecorder.isTypeSupported" in script
    assert "state.maxDurationMs = Number(status.max_voice_duration_ms)" in script
    assert "window.setTimeout(finishRecording, state.maxDurationMs)" in script
    assert "5 * 1024 * 1024" in script
    assert 'fetch("/linkup/voice"' in script
    assert "credentials: \"same-origin\"" in script
    assert "cache: \"no-store\"" in script
    assert "http://" not in script
    assert "https://" not in script
    assert "navigator.mediaDevices.enumerateDevices" not in script
    assert "video: true" not in script


def test_voice_permission_is_requested_from_click_path_not_page_load():
    script = SCRIPT.read_text(encoding="utf-8")

    assert "const startRecording = async (control) =>" in script
    assert 'control.addEventListener("click", () => startRecording(control))' in script
    assert "getUserMedia" in script
    assert 'apiJson("/linkup/voice/status")' in script


def test_voice_browser_controller_has_valid_javascript_syntax():
    node = shutil.which("node")
    if node is None:
        return

    subprocess.run(
        [node, "--check", str(SCRIPT)],
        check=True,
        capture_output=True,
        text=True,
    )
