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
