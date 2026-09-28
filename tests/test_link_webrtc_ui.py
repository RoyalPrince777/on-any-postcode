from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_webrtc_controller_has_valid_javascript_syntax():
    node = shutil.which("node")
    if node is None:
        return
    subprocess.run(
        [node, "--check", str(ROOT / "static" / "linkup_realtime.js")],
        check=True,
        capture_output=True,
        text=True,
    )


def test_webrtc_controller_uses_only_first_party_runtime_gates():
    source = (ROOT / "static" / "linkup_realtime.js").read_text(encoding="utf-8")

    for required in (
        'api("/linkup/calls/status")',
        'api("/linkup/signalling/status")',
        'api("/linkup/turn/status")',
        'api("/linkup/turn/credentials"',
        'api("/linkup/calls"',
        'api("/linkup/calls/active")',
        'api("/linkup/signalling/events"',
        "turn.relay_verified",
        "calls.records_media === false",
    ):
        assert required in source

    for forbidden in (
        "https://",
        "http://",
        "stun:",
        "google",
        "MediaRecorder",
        "enumerateDevices",
    ):
        assert forbidden not in source


def test_webrtc_media_permission_is_not_requested_during_readiness_check():
    source = (ROOT / "static" / "linkup_realtime.js").read_text(encoding="utf-8")
    before_session_open = source.split("const openPeerSession", maxsplit=1)[0]

    assert "getUserMedia({" not in before_session_open
    assert "navigator.mediaDevices.getUserMedia({" in source
    assert 'video: mode === "face_up"' in source
    assert "audio: true" in source


def test_webrtc_constructor_failure_stops_captured_media_before_rethrow():
    source = (ROOT / "static" / "linkup_realtime.js").read_text(encoding="utf-8")
    acquired = source.index("const localStream = await navigator.mediaDevices.getUserMedia(")
    constructor = source.index("pc = new RTCPeerConnection(", acquired)
    cleanup = source.index("localStream.getTracks().forEach((track) => track.stop());", constructor)
    rethrow = source.index("throw error;", cleanup)
    state_assignment = source.index("state.localStream = localStream;", rethrow)
    assert acquired < constructor < cleanup < rethrow < state_assignment
    assert "catch (error) {" in source[constructor:cleanup]


def test_webrtc_controls_render_locked_and_recipient_scoped():
    template = (
        ROOT / "mission_control" / "templates" / "linkup.html"
    ).read_text(encoding="utf-8")

    assert '<meta name="oap-csrf-token" content="{{ oap_csrf_token }}">' in template
    assert "disabled data-oap-call-control data-call-mode=\"call\"" in template
    assert "disabled data-oap-call-control data-call-mode=\"face_up\"" in template
    assert 'data-recipient-source="#linkup-recipient"' in template
    assert 'data-recipient-id="{{ thread.other_identity_id }}"' in template
    assert "data-oap-incoming-calls" in template
    assert "data-oap-call-stage" in template
    assert "data-oap-hangup" in template


def test_link_call_media_acceptance_contract_is_complete():
    source = (ROOT / "static" / "linkup_realtime.js").read_text(encoding="utf-8")
    template = (
        ROOT / "mission_control" / "templates" / "linkup.html"
    ).read_text(encoding="utf-8")

    # Browser capability and explicit capture.
    assert 'typeof window.RTCPeerConnection === "function"' in source
    assert "navigator.mediaDevices?.getUserMedia" in source
    assert "audio: true" in source
    assert 'video: mode === "face_up"' in source

    # Local preview and remote playback paths.
    assert "localVideo.srcObject = localStream;" in source
    assert "remoteVideo.srcObject = stream;" in source
    assert "remoteAudio.srcObject = stream;" in source
    assert "<video data-oap-remote-video autoplay playsinline hidden></video>" in template
    assert "<video data-oap-local-video autoplay muted playsinline hidden></video>" in template
    assert "<audio data-oap-remote-audio autoplay hidden></audio>" in template

    # Every local track is explicitly stopped during teardown and constructor failure.
    assert "state.localStream.getTracks().forEach((track) => track.stop());" in source
    assert "localStream.getTracks().forEach((track) => track.stop());" in source
    assert 'window.addEventListener("pagehide"' in source
    assert "stopLocalMedia();" in source
    assert "state.pc.close();" in source

    # Call media is not recorded or persisted by this WebRTC controller.
    assert "MediaRecorder" not in source
    assert "calls.records_media === false" in source

    # Public naming is Link Call while the internal compatibility mode stays face_up.
    for stale in (
        "Face Up is ringing",
        "Starting Face Up",
        "Answering Face Up",
        "Incoming Face Up",
        "Call and Face Up",
    ):
        assert stale not in source
    assert "Link Call connected." in source
    assert "Starting Link Call" in source
    assert "Incoming Link Call" in source


def test_link_call_permissions_policy_is_scoped_to_linkup():
    security = (
        ROOT / "mission_control" / "surface_security.py"
    ).read_text(encoding="utf-8")
    assert '_LINK_DEVICE_PATHS = frozenset({"/linkup"})' in security
    assert '"camera=(self), microphone=(self), geolocation=(self), payment=()"' in security
    assert 'response.headers["Permissions-Policy"] = _LINK_PERMISSIONS_POLICY' in security
