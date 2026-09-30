"""PTT is a bounded hold/release adapter over existing governed Voice, not live radio."""
import shutil
import subprocess
from pathlib import Path

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


def test_ptt_event_listeners_are_not_registered_during_refresh():
    script = SCRIPT.read_text(encoding="utf-8")
    refresh = script.split("const refreshControls = () => {", maxsplit=1)[1].split("const stopTracks =", maxsplit=1)[0]
    assert "addEventListener" not in refresh
    assert "const beginPtt" not in refresh
    assert script.count('control.addEventListener("pointerdown"') == 1
    assert script.index("const startRecording = async") < script.index("const beginPtt =")
    assert script.index("const beginPtt =") < script.index('control.addEventListener("pointerdown"')
    assert 'window.addEventListener("blur", () => endPtt(true))' in script
    assert 'document.addEventListener("visibilitychange"' in script


def test_voice_and_ptt_capture_are_serialised_during_pending_permission():
    source = SCRIPT.read_text(encoding="utf-8")
    assert "capturePending: false" in source
    assert "state.capturePending = true;" in source
    assert "state.capturePending = false;" in source
    assert "state.current || state.capturePending || !browserReady()" in source
    assert "state.pttPress || state.current || state.capturePending" in source
    assert "Boolean(state.pttPress) || state.capturePending" in source
    # Both success and exception branches release the pending-capture lock.
    assert source.index("state.capturePending = false;", source.index("getUserMedia({ audio: true")) < source.index("new MediaRecorder(stream")
    catch = source.split("} catch (error) {", maxsplit=2)[-1]
    assert "state.capturePending = false;" in catch


def test_ptt_controller_behaviour_with_mock_media_and_events():
    node = shutil.which("node")
    if node is None:
        return
    subprocess.run(
        [node, str(ROOT / "tests" / "link_ptt_behavior.cjs")],
        check=True,
        capture_output=True,
        text=True,
        timeout=15,
    )
