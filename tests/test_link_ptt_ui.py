"""PTT is a bounded hold/release adapter over existing governed Voice, not live radio."""
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "static" / "linkup_voice.js"
TEMPLATE = ROOT / "mission_control" / "templates" / "linkup.html"
NETWORK = ROOT / "static" / "linkup_network.js"


def test_ptt_is_private_recipient_scoped_and_in_voice_composer():
    template = TEMPLATE.read_text(encoding="utf-8")
    assert 'data-oap-ptt-control data-recipient-id="{{ thread.other_identity_id }}"' in template
    assert 'disabled data-oap-ptt-control' in template
    assert 'aria-label="Hold to talk"' in template
    assert 'data-oap-voice-control' in template
    assert 'data-oap-voice-stop' in template


def test_ptt_hold_release_cancel_and_keyboard_are_bound():
    src = SCRIPT.read_text(encoding="utf-8")
    for required in (
        'control.addEventListener("pointerdown"',
        'window.addEventListener("pointerup", () => endPtt())',
        'window.addEventListener("pointercancel", () => endPtt(true))',
        'control.addEventListener("keydown"',
        'control.addEventListener("keyup"',
        'control.addEventListener("blur"',
        'event.repeat',
        'state.pttPress',
        'press.released = true',
        'press.cancelled = true',
        'if (cancel) state.current.cancelled = true',
        'if (pttPress?.released) finishRecording()',
        'state.pttPress !== pttPress || pttPress.cancelled',
        'stopTracks(stream)',
        'endPtt(true)',
        'control.setAttribute("aria-pressed", String(active))',
    ):
        assert required in src


def test_ptt_reuses_first_party_voice_and_offline_guard():
    src = SCRIPT.read_text(encoding="utf-8")
    network = NETWORK.read_text(encoding="utf-8")
    assert 'startRecording(control, press)' in src
    assert 'fetch("/linkup/voice"' in src
    assert 'credentials: "same-origin"' in src
    assert '"X-OAP-CSRF": csrfToken' in src
    assert '"[data-oap-ptt-control]"' in network
    assert "new WebSocket" not in src
    assert "https://" not in src


def test_ptt_controller_javascript_syntax():
    node = shutil.which("node")
    if node is None:
        return
    subprocess.run([node, "--check", str(SCRIPT)], check=True, capture_output=True, text=True)
