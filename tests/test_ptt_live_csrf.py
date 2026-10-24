"""PTT WebRTC signalling must use the exact first-party CSRF header.

These tests prove the Flask contract and do not claim live media transport.
"""
from __future__ import annotations

import uuid

from mission_control import ptt_routes, web_security


def _session(client):
    identity = str(uuid.uuid4())
    token = "oap-ptt-signalling-csrf-token-1234567890"
    with client.session_transaction() as state:
        state[ptt_routes.PTT_GUEST_ID_KEY] = identity
        state[web_security.CSRF_SESSION_KEY] = token
    return identity, token


def test_ptt_signalling_rejects_wrong_csrf_header(anonymous_client, monkeypatch):
    _identity, token = _session(anonymous_client)
    touched = []
    monkeypatch.setattr(
        ptt_routes.ptt_signalling, "send",
        lambda *args: touched.append(args) or "should-not-send",
    )
    payload = {"kind": "offer", "payload": {"type": "offer", "sdp": "v=0\r\n"}}
    wrong = anonymous_client.post(
        "/ptt/live/signal", json=payload, headers={"X-CSRF-Token": token}
    )
    assert wrong.status_code == 403
    assert wrong.get_json()["error"]["code"] == "csrf_failed"
    assert wrong.headers["Cache-Control"] == "no-store"
    assert touched == []


def test_ptt_signalling_accepts_canonical_csrf_and_session(anonymous_client, monkeypatch):
    identity, token = _session(anonymous_client)
    observed = []
    signal_id = str(uuid.uuid4())
    monkeypatch.setattr(
        ptt_routes.ptt_signalling, "send",
        lambda *args: observed.append(args) or signal_id,
    )
    payload = {"kind": "offer", "payload": {"type": "offer", "sdp": "v=0\r\n"}}
    response = anonymous_client.post(
        "/ptt/live/signal", json=payload, headers={"X-OAP-CSRF": token}
    )
    assert response.status_code == 202
    assert response.get_json() == {"id": signal_id}
    assert observed == [(identity, "offer", payload["payload"])]
    assert response.headers["Cache-Control"] == "no-store"


def test_ptt_signalling_rejects_missing_guest_session(anonymous_client, monkeypatch):
    token = "oap-ptt-signalling-csrf-token-1234567890"
    with anonymous_client.session_transaction() as state:
        state[web_security.CSRF_SESSION_KEY] = token
    observed = []
    monkeypatch.setattr(
        ptt_routes.ptt_signalling, "send",
        lambda *args: observed.append(args),
    )
    response = anonymous_client.post(
        "/ptt/live/signal",
        json={"kind": "hangup", "payload": {}},
        headers={"X-OAP-CSRF": token},
    )
    assert response.status_code == 403
    assert response.get_json()["error"]["code"] == "ptt_pair_required"
    assert observed == []


def test_ptt_pairing_does_not_claim_live_audio_ready(anonymous_client, monkeypatch):
    _identity, _token = _session(anonymous_client)
    monkeypatch.setattr(
        ptt_routes.ptt_guest, "invite_state",
        lambda value, _code: {
            "active": True,
            "identity_id": value,
            "peer_id": str(uuid.uuid4()),
        },
    )
    status = anonymous_client.get("/ptt/live/status").get_json()
    assert status["paired"] is True
    assert status["live_ready"] is False
    assert status["media_ready"] is False
    assert status["recording_enabled"] is False
