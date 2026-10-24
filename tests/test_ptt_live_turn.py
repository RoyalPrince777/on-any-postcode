"""PTT borrows only OAP's verified TURN issuer, scoped to a live guest pair.

Mocks exercise the authenticated/authorised contract, not a public relay or
two-device audio connection.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import uuid

from mission_control import link_turn, ptt_routes, web_security


def _pair_session(anonymous_client, monkeypatch, *, active=True):
    identity = str(uuid.uuid4())
    recipient = str(uuid.uuid4())
    token = "ptt-turn-first-party-csrf-1234567890"
    with anonymous_client.session_transaction() as state:
        state[ptt_routes.PTT_GUEST_ID_KEY] = identity
        state[web_security.CSRF_SESSION_KEY] = token
    monkeypatch.setattr(
        ptt_routes.ptt_guest,
        "invite_state",
        lambda value, _code: {
            "active": active,
            "identity_id": value,
            "peer_id": recipient if active else None,
        },
    )
    return identity, recipient, token


def _post(client, token, *, header="X-OAP-CSRF"):
    return client.post("/ptt/live/ice", json={}, headers={header: token})


def test_ptt_turn_credentials_require_temporary_pair(anonymous_client, monkeypatch):
    token = "ptt-turn-first-party-csrf-1234567890"
    with anonymous_client.session_transaction() as state:
        state[web_security.CSRF_SESSION_KEY] = token
    monkeypatch.setattr(
        ptt_routes.link_turn,
        "issue_credentials",
        lambda *_args: (_ for _ in ()).throw(AssertionError("issuer should not run")),
    )
    result = _post(anonymous_client, token)
    assert result.status_code == 403
    assert result.get_json()["error"]["code"] == "ptt_pair_required"


def test_ptt_turn_credentials_require_canonical_csrf_header(anonymous_client, monkeypatch):
    _identity, _peer, token = _pair_session(anonymous_client, monkeypatch)
    monkeypatch.setattr(
        ptt_routes.link_turn,
        "issue_credentials",
        lambda *_args: (_ for _ in ()).throw(AssertionError("issuer should not run")),
    )
    wrong = _post(anonymous_client, token, header="X-CSRF-Token")
    assert wrong.status_code == 403
    assert wrong.get_json()["error"]["code"] == "csrf_failed"


def test_ptt_turn_refuses_inactive_pair_before_issuer(anonymous_client, monkeypatch):
    _identity, _peer, token = _pair_session(anonymous_client, monkeypatch, active=False)
    monkeypatch.setattr(
        ptt_routes.link_turn,
        "issue_credentials",
        lambda *_args: (_ for _ in ()).throw(AssertionError("issuer should not run")),
    )
    result = _post(anonymous_client, token)
    assert result.status_code == 403
    assert result.get_json()["error"]["code"] == "ptt_pair_required"


def test_ptt_turn_unverified_relay_blocks_credentials(anonymous_client, monkeypatch):
    _identity, _peer, token = _pair_session(anonymous_client, monkeypatch)
    monkeypatch.setattr(ptt_routes.link_turn, "status", lambda: {
        "credential_ready": True, "relay_verified": False
    })
    monkeypatch.setattr(
        ptt_routes.link_turn,
        "issue_credentials",
        lambda *_args: (_ for _ in ()).throw(AssertionError("issuer should not run")),
    )
    result = _post(anonymous_client, token)
    assert result.status_code == 503
    assert result.get_json()["error"]["code"] == "ptt_turn_unverified"
    assert result.headers["Cache-Control"] == "no-store"
    assert "ice_servers" not in result.get_data(as_text=True)


def test_ptt_turn_credentials_use_existing_signed_oap_issuer(anonymous_client, monkeypatch):
    identity, peer, token = _pair_session(anonymous_client, monkeypatch)
    monkeypatch.setenv(
        "OAP_LINK_TURN_URLS", "turn:turn.oap.internal:3478?transport=udp"
    )
    secret = "OAP-private-test-secret-" + ("z" * 48)
    monkeypatch.setenv("OAP_LINK_TURN_SHARED_SECRET", secret)
    monkeypatch.setenv("OAP_LINK_TURN_REALM", "turn.oap.internal")
    monkeypatch.setenv("OAP_LINK_TURN_OWNED", "true")
    monkeypatch.setenv("OAP_LINK_TURN_RELAY_VERIFIED", "true")
    monkeypatch.setenv("OAP_LINK_TURN_TTL_SECONDS", "300")
    now_before = int(link_turn.time.time())
    checked = []
    monkeypatch.setattr(
        link_turn.linkup_safety,
        "blocked_between",
        lambda first, second: checked.append(("block", first, second)) or False,
    )
    monkeypatch.setattr(
        link_turn.link_relationships,
        "accepted_between",
        lambda first, second: checked.append(("accepted", first, second)) or True,
    )
    result = _post(anonymous_client, token)
    assert result.status_code == 200
    assert result.headers["Cache-Control"] == "no-store"
    assert result.headers["X-Content-Type-Options"] == "nosniff"
    payload = result.get_json()
    assert payload["relay_verified"] is True
    now_after = int(link_turn.time.time())
    assert now_before + 300 <= payload["expires_at"] <= now_after + 300
    assert payload["ttl_seconds"] == 300
    server = payload["ice_servers"][0]
    username = f"{payload['expires_at']}:{identity}"
    assert server["username"] == username
    assert server["urls"] == ["turn:turn.oap.internal:3478?transport=udp"]
    assert server["credential"] == base64.b64encode(
        hmac.new(secret.encode(), username.encode(), hashlib.sha1).digest()
    ).decode("ascii")
    assert checked == [("block", identity, peer), ("accepted", identity, peer)]
    assert secret not in result.get_data(as_text=True)


def test_ptt_turn_blocked_peer_returns_forbidden(anonymous_client, monkeypatch):
    _identity, _peer, token = _pair_session(anonymous_client, monkeypatch)
    monkeypatch.setattr(
        ptt_routes.link_turn, "status", lambda: {"relay_verified": True}
    )
    monkeypatch.setattr(
        ptt_routes.link_turn,
        "issue_credentials",
        lambda *_args: (_ for _ in ()).throw(ValueError("link_blocked")),
    )
    result = _post(anonymous_client, token)
    assert result.status_code == 403
    assert result.get_json()["error"]["code"] == "link_blocked"


def test_ptt_turn_unavailable_does_not_leak_secret(anonymous_client, monkeypatch):
    _identity, _peer, token = _pair_session(anonymous_client, monkeypatch)
    monkeypatch.setattr(
        ptt_routes.link_turn, "status", lambda: {"relay_verified": True}
    )
    monkeypatch.setattr(
        ptt_routes.link_turn,
        "issue_credentials",
        lambda *_args: (_ for _ in ()).throw(
            link_turn.LinkTurnUnavailable("private-secret-should-not-leak")
        ),
    )
    result = _post(anonymous_client, token)
    assert result.status_code == 503
    assert result.get_json()["error"]["code"] == "ptt_turn_unavailable"
    assert "private-secret" not in result.get_data(as_text=True)


def test_ptt_turn_never_promotes_pairing_to_live_readiness(anonymous_client, monkeypatch):
    _identity, _peer, _token = _pair_session(anonymous_client, monkeypatch)
    response = anonymous_client.get("/ptt/live/status")
    state = response.get_json()
    assert state["paired"] is True
    assert state["live_ready"] is False
    assert state["signalling_ready"] is False
    assert state["media_ready"] is False
